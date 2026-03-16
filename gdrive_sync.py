#!/usr/bin/env python3
"""
Google Drive Sync Agent for Antigravity
========================================
Sincroniza os dados do Antigravity (brain/, knowledge/, conversations/)
com uma pasta no Google Drive, permitindo compartilhar histórico entre
dois computadores.

Uso:
    python gdrive_sync.py auth      # Autenticar com Google Drive
    python gdrive_sync.py push      # Upload de arquivos locais para o Drive
    python gdrive_sync.py pull      # Download de arquivos do Drive para local
    python gdrive_sync.py sync      # Bidirecional: pull + push
    python gdrive_sync.py status    # Mostra status da sincronização
    python gdrive_sync.py updates   # Gerenciar atualizações gerais
"""

import os
import sys
import json
import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path

# Fix Windows console encoding for emoji/unicode output
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io
import logging

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

SCOPES = ['https://www.googleapis.com/auth/drive.file']
DRIVE_FOLDER_NAME = 'Antigravity-Sync'
ANTIGRAVITY_BASE = Path.home() / '.gemini' / 'antigravity'
SYNC_DIR = Path(__file__).parent
TOKEN_PATH = SYNC_DIR / 'token.json'
CREDENTIALS_PATH = SYNC_DIR / 'credentials.json'
SYNC_STATE_PATH = SYNC_DIR / 'sync_state.json'
BACKUP_DIR = SYNC_DIR / 'backups'
GENERAL_UPDATES_DIR = ANTIGRAVITY_BASE / 'updates'
AUDIT_LOG_PATH = SYNC_DIR / 'sync_audit.log'

# Pastas do Antigravity a sincronizar
SYNC_FOLDERS = ['brain', 'knowledge', 'conversations', 'updates']

# Extensões/arquivos a ignorar
IGNORE_PATTERNS = [
    '__pycache__',
    '.lock',
    'knowledge.lock',
    '.tmp',
    '.DS_Store',
    'Thumbs.db',
]

# ============================================================================
# SEGURANÇA: Flags globais
# ============================================================================

DRY_RUN = '--dry-run' in sys.argv
AUTO_APPROVE = '--yes' in sys.argv

# POLÍTICA: Nenhum arquivo é excluído automaticamente.
# Apenas uploads e downloads são permitidos.
# Exclusões requerem aprovação explícita.
NO_DELETE_POLICY = True


# ============================================================================
# UTILITÁRIOS
# ============================================================================

class Colors:
    """ANSI color codes para output bonito."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def log(msg, color=Colors.CYAN):
    """Print colorido."""
    print(f"{color}  {msg}{Colors.END}")


def log_success(msg):
    log(msg, Colors.GREEN)


def log_warn(msg):
    log(f"⚠️  {msg}", Colors.WARNING)


def log_error(msg):
    log(f"❌ {msg}", Colors.FAIL)


def log_header(msg):
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}{Colors.END}\n")


# ============================================================================
# AUDITORIA E SEGURANÇA
# ============================================================================

def setup_audit_log():
    """Configura log de auditoria para rastrear todas as operações."""
    audit_logger = logging.getLogger('sync_audit')
    audit_logger.setLevel(logging.INFO)
    handler = logging.FileHandler(str(AUDIT_LOG_PATH), encoding='utf-8')
    handler.setFormatter(logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    audit_logger.addHandler(handler)
    return audit_logger


audit = setup_audit_log()


def confirm_action(action_description: str, details: list = None) -> bool:
    """
    Solicita confirmação do usuário antes de executar ações.
    Retorna True se aprovado, False se recusado.
    """
    if AUTO_APPROVE:
        audit.info(f'AUTO-APROVADO: {action_description}')
        return True

    if DRY_RUN:
        log(f"  [DRY-RUN] {action_description}", Colors.WARNING)
        if details:
            for d in details:
                log(f"    → {d}", Colors.CYAN)
        return False

    log(f"\n🔒 APROVAÇÃO NECESSÁRIA:", Colors.WARNING)
    log(f"   {action_description}", Colors.BOLD)
    if details:
        for d in details:
            log(f"    → {d}", Colors.CYAN)

    try:
        resp = input(f"\n   Confirmar? [s/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        resp = 'n'

    approved = resp in ('s', 'sim', 'y', 'yes')
    status = 'APROVADO' if approved else 'RECUSADO'
    audit.info(f'{status}: {action_description}')

    if not approved:
        log("   ❌ Operação cancelada pelo usuário.", Colors.FAIL)

    return approved


def should_ignore(path: Path) -> bool:
    """Verifica se o arquivo/pasta deve ser ignorado."""
    name = path.name
    for pattern in IGNORE_PATTERNS:
        if pattern in str(path) or name == pattern:
            return True
    return False


def file_hash(filepath: Path) -> str:
    """Calcula MD5 hash de um arquivo."""
    h = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def load_sync_state() -> dict:
    """Carrega estado de sincronização anterior."""
    if SYNC_STATE_PATH.exists():
        with open(SYNC_STATE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'files': {}, 'last_sync': None}


def save_sync_state(state: dict):
    """Salva estado de sincronização."""
    state['last_sync'] = datetime.now(timezone.utc).isoformat()
    with open(SYNC_STATE_PATH, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


# ============================================================================
# AUTENTICAÇÃO GOOGLE DRIVE
# ============================================================================

def authenticate():
    """Autentica com Google Drive via OAuth2."""
    creds = None

    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            log("Renovando token de acesso...")
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                log_error(
                    f"Arquivo credentials.json não encontrado em:\n"
                    f"   {CREDENTIALS_PATH}\n\n"
                    f"   Siga as instruções em setup_credentials.md para configurar."
                )
                sys.exit(1)

            log("Abrindo navegador para autenticação...")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH), SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
        log_success("Token salvo com sucesso!")

    return creds


def get_drive_service():
    """Retorna instância do serviço Google Drive."""
    creds = authenticate()
    return build('drive', 'v3', credentials=creds)


# ============================================================================
# OPERAÇÕES NO GOOGLE DRIVE
# ============================================================================

def get_or_create_folder(service, folder_name, parent_id=None):
    """Busca ou cria uma pasta no Google Drive."""
    query = (
        f"name='{folder_name}' and "
        f"mimeType='application/vnd.google-apps.folder' and "
        f"trashed=false"
    )
    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = service.files().list(
        q=query, spaces='drive', fields='files(id, name)'
    ).execute()

    files = results.get('files', [])

    if files:
        return files[0]['id']

    # Criar pasta
    metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_id:
        metadata['parents'] = [parent_id]

    folder = service.files().create(body=metadata, fields='id').execute()
    log_success(f"Pasta criada no Drive: {folder_name}")
    return folder['id']


def get_drive_root_folder(service):
    """Obtém ou cria a pasta raiz Antigravity-Sync no Drive."""
    return get_or_create_folder(service, DRIVE_FOLDER_NAME)


def ensure_drive_path(service, root_id, relative_path: Path):
    """Garante que o caminho de diretórios existe no Drive. Retorna o ID da pasta final."""
    current_id = root_id
    for part in relative_path.parts:
        current_id = get_or_create_folder(service, part, current_id)
    return current_id


def find_file_in_drive(service, filename, parent_id):
    """Busca um arquivo específico em uma pasta do Drive."""
    query = (
        f"name='{filename}' and "
        f"'{parent_id}' in parents and "
        f"trashed=false"
    )
    results = service.files().list(
        q=query, spaces='drive',
        fields='files(id, name, modifiedTime, md5Checksum, size)'
    ).execute()
    files = results.get('files', [])
    return files[0] if files else None


def upload_file(service, local_path: Path, parent_id: str, relative_path: str):
    """Faz upload de um arquivo para o Drive."""
    filename = local_path.name
    existing = find_file_in_drive(service, filename, parent_id)

    media = MediaFileUpload(str(local_path), resumable=True)

    if existing:
        # Atualizar arquivo existente
        service.files().update(
            fileId=existing['id'],
            media_body=media
        ).execute()
        log(f"  ⬆️  Atualizado: {relative_path}")
    else:
        # Criar novo arquivo
        metadata = {
            'name': filename,
            'parents': [parent_id]
        }
        service.files().create(
            body=metadata, media_body=media, fields='id'
        ).execute()
        log(f"  ⬆️  Enviado:    {relative_path}")


def download_file(service, file_id: str, local_path: Path, relative_path: str):
    """Baixa um arquivo do Drive para o local."""
    local_path.parent.mkdir(parents=True, exist_ok=True)

    request = service.files().get_media(fileId=file_id)
    with open(local_path, 'wb') as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

    log(f"  ⬇️  Baixado:    {relative_path}")


def list_drive_files_recursive(service, folder_id, prefix=""):
    """Lista todos os arquivos recursivamente em uma pasta do Drive."""
    files_list = []
    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(
        q=query, spaces='drive',
        fields='files(id, name, mimeType, modifiedTime, md5Checksum, size)',
        pageSize=1000
    ).execute()

    for item in results.get('files', []):
        item_path = f"{prefix}/{item['name']}" if prefix else item['name']

        if item['mimeType'] == 'application/vnd.google-apps.folder':
            files_list.extend(
                list_drive_files_recursive(service, item['id'], item_path)
            )
        else:
            item['relativePath'] = item_path
            files_list.append(item)

    return files_list


# ============================================================================
# BACKUP E FLAG DE REAVALIAÇÃO
# ============================================================================

def create_backup():
    """Cria um backup local antes de sincronizar."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = BACKUP_DIR / timestamp
    backup_path.mkdir(parents=True, exist_ok=True)

    for folder in SYNC_FOLDERS:
        src = ANTIGRAVITY_BASE / folder
        if src.exists():
            dst = backup_path / folder
            shutil.copytree(src, dst, dirs_exist_ok=True)

    log_success(f"Backup criado em: {backup_path}")
    return backup_path


def create_reavaliar_flag(backup_path: Path, changes: list):
    """
    Cria arquivo _01_reavaliar na pasta de backup quando houve atualizações,
    para sinalizar que os dados devem ser reavaliados.
    """
    if not changes:
        return

    flag_path = backup_path / '_01_reavaliar'
    content = (
        f"⚠️ REAVALIAÇÃO NECESSÁRIA\n"
        f"{'='*50}\n"
        f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Motivo: Foram detectadas atualizações durante a sincronização.\n"
        f"\nArquivos alterados:\n"
    )
    for change in changes:
        content += f"  - {change}\n"

    content += (
        f"\nAção recomendada:\n"
        f"  Revisar os arquivos alterados para garantir que\n"
        f"  nenhum dado importante foi sobrescrito.\n"
    )

    with open(flag_path, 'w', encoding='utf-8') as f:
        f.write(content)

    log_warn(f"Flag _01_reavaliar criado em: {flag_path}")


# ============================================================================
# COMANDOS PRINCIPAIS
# ============================================================================

def cmd_auth():
    """Comando: autenticar com Google Drive."""
    log_header("🔐 Autenticação Google Drive")
    service = get_drive_service()
    root_id = get_drive_root_folder(service)
    log_success(f"Autenticado com sucesso!")
    log_success(f"Pasta raiz no Drive: {DRIVE_FOLDER_NAME} (ID: {root_id})")


def cmd_push():
    """Comando: upload de arquivos locais para o Drive."""
    log_header("⬆️  PUSH - Enviando dados para o Google Drive")

    if DRY_RUN:
        log("🔍 MODO DRY-RUN: nenhuma alteração será feita.\n", Colors.WARNING)

    service = get_drive_service()
    root_id = get_drive_root_folder(service)
    state = load_sync_state()
    pending_changes = []
    changes = []
    file_count = 0

    # Fase 1: Coletar mudanças
    for folder_name in SYNC_FOLDERS:
        local_folder = ANTIGRAVITY_BASE / folder_name
        if not local_folder.exists():
            log_warn(f"Pasta não encontrada: {local_folder}")
            continue

        log(f"\n📁 Verificando: {folder_name}/", Colors.BOLD)

        for filepath in local_folder.rglob('*'):
            if filepath.is_dir() or should_ignore(filepath):
                continue

            relative = filepath.relative_to(ANTIGRAVITY_BASE)
            relative_str = str(relative).replace('\\', '/')

            current_hash = file_hash(filepath)
            last_hash = state['files'].get(relative_str, {}).get('hash', '')

            if current_hash == last_hash:
                continue

            pending_changes.append((filepath, relative, relative_str, current_hash))

    if not pending_changes:
        log_success("\n✅ Nenhuma alteração detectada. Tudo sincronizado.")
        return

    # Fase 2: Listar e aprovar
    log(f"\n📋 {len(pending_changes)} arquivo(s) para enviar:", Colors.BOLD)
    for _, _, rel_str, _ in pending_changes:
        log(f"    ⬆️  {rel_str}")

    if not confirm_action(
        f"Enviar {len(pending_changes)} arquivo(s) para o Google Drive?",
        [r for _, _, r, _ in pending_changes]
    ):
        return

    # Fase 3: Executar uploads aprovados
    for filepath, relative, relative_str, current_hash in pending_changes:
        parent_relative = relative.parent
        parent_id = ensure_drive_path(service, root_id, parent_relative)
        upload_file(service, filepath, parent_id, relative_str)
        audit.info(f'PUSH: {relative_str} (hash: {current_hash})')

        state['files'][relative_str] = {
            'hash': current_hash,
            'last_push': datetime.now(timezone.utc).isoformat(),
            'size': filepath.stat().st_size
        }
        changes.append(f"PUSH: {relative_str}")
        file_count += 1

    save_sync_state(state)

    if file_count > 0:
        log(f"\n📦 Criando backup de releitura...")
        backup_path = create_backup()
        create_reavaliar_flag(backup_path, changes)

    log_success(f"\n✅ Push completo! {file_count} arquivo(s) enviado(s).")


def cmd_pull():
    """Comando: download de arquivos do Drive para o local."""
    log_header("⬇️  PULL - Baixando dados do Google Drive")

    if DRY_RUN:
        log("🔍 MODO DRY-RUN: nenhuma alteração será feita.\n", Colors.WARNING)

    service = get_drive_service()
    root_id = get_drive_root_folder(service)
    state = load_sync_state()
    changes = []
    file_count = 0

    drive_files = list_drive_files_recursive(service, root_id)

    if not drive_files:
        log("Nenhum arquivo encontrado no Drive para baixar.")
        return

    log(f"Encontrados {len(drive_files)} arquivo(s) no Drive.\n")

    # Fase 1: Coletar arquivos para download
    pending_downloads = []

    for drive_file in drive_files:
        relative_path = drive_file['relativePath']

        if any(p in relative_path for p in IGNORE_PATTERNS):
            continue

        local_path = ANTIGRAVITY_BASE / relative_path.replace('/', os.sep)
        should_download = False
        reason = ''

        if not local_path.exists():
            should_download = True
            reason = 'NOVO'
        else:
            local_h = file_hash(local_path)
            drive_checksum = drive_file.get('md5Checksum', '')

            if drive_checksum and local_h != drive_checksum:
                drive_modified = drive_file.get('modifiedTime', '')
                local_modified = datetime.fromtimestamp(
                    local_path.stat().st_mtime, tz=timezone.utc
                ).isoformat()

                if drive_modified > local_modified:
                    should_download = True
                    reason = 'ATUALIZADO'
                else:
                    log_warn(
                        f"  Conflito: {relative_path} "
                        f"(local mais recente, mantendo local)"
                    )

        if should_download:
            pending_downloads.append((drive_file, local_path, relative_path, reason))

    if not pending_downloads:
        log_success("\n✅ Nenhuma alteração detectada. Tudo sincronizado.")
        return

    # Fase 2: Listar e aprovar
    log(f"\n📋 {len(pending_downloads)} arquivo(s) para baixar:", Colors.BOLD)
    for _, _, rp, reason in pending_downloads:
        log(f"    ⬇️  [{reason}] {rp}")

    if not confirm_action(
        f"Baixar {len(pending_downloads)} arquivo(s) do Google Drive?",
        [f'[{r}] {rp}' for _, _, rp, r in pending_downloads]
    ):
        return

    # Fase 3: Executar downloads aprovados
    for drive_file, local_path, relative_path, reason in pending_downloads:
        download_file(service, drive_file['id'], local_path, relative_path)
        audit.info(f'PULL [{reason}]: {relative_path}')

        state['files'][relative_path] = {
            'hash': file_hash(local_path) if local_path.exists() else '',
            'last_pull': datetime.now(timezone.utc).isoformat(),
            'size': int(drive_file.get('size', 0))
        }
        changes.append(f"PULL: {relative_path}")
        file_count += 1

    save_sync_state(state)

    if file_count > 0:
        log(f"\n📦 Criando backup de releitura...")
        backup_path = create_backup()
        create_reavaliar_flag(backup_path, changes)

    log_success(f"\n✅ Pull completo! {file_count} arquivo(s) baixado(s).")


def cmd_sync():
    """Comando: sincronização bidirecional (pull + push)."""
    log_header("🔄 SYNC - Sincronização Bidirecional")
    log("Etapa 1/2: Pull (baixar do Drive)...")
    cmd_pull()
    log("\nEtapa 2/2: Push (enviar para o Drive)...")
    cmd_push()
    log_header("🔄 Sincronização completa!")


def cmd_status():
    """Comando: mostra status da sincronização."""
    log_header("📊 Status da Sincronização")

    state = load_sync_state()

    if state['last_sync']:
        log(f"Último sync: {state['last_sync']}")
    else:
        log("Nenhuma sincronização realizada ainda.")

    log(f"Arquivos rastreados: {len(state['files'])}")

    # Verificar token
    if TOKEN_PATH.exists():
        log_success("Autenticação: ✅ Token encontrado")
    else:
        log_warn("Autenticação: ❌ Não autenticado (execute: python gdrive_sync.py auth)")

    # Verificar credentials
    if CREDENTIALS_PATH.exists():
        log_success("Credenciais: ✅ credentials.json encontrado")
    else:
        log_error("Credenciais: ❌ credentials.json não encontrado")

    # Verificar pastas locais
    log(f"\n📁 Pastas locais:", Colors.BOLD)
    for folder in SYNC_FOLDERS:
        path = ANTIGRAVITY_BASE / folder
        if path.exists():
            count = sum(1 for _ in path.rglob('*') if _.is_file())
            log_success(f"  {folder}/: {count} arquivo(s)")
        else:
            log_warn(f"  {folder}/: não encontrada")

    # Verificar backups
    if BACKUP_DIR.exists():
        backups = sorted(BACKUP_DIR.iterdir())
        log(f"\n📦 Backups: {len(backups)}", Colors.BOLD)
        for b in backups[-3:]:  # Mostrar últimos 3
            has_flag = (b / '_01_reavaliar').exists()
            flag_str = " ⚠️ REAVALIAR" if has_flag else ""
            log(f"  {b.name}{flag_str}")
    else:
        log("\n📦 Nenhum backup encontrado.")


def cmd_updates():
    """Comando: gerenciar atualizações gerais compartilhadas."""
    log_header("📝 Atualizações Gerais")

    # Criar pasta de updates se não existir
    GENERAL_UPDATES_DIR.mkdir(parents=True, exist_ok=True)

    # Subcomandos
    action = sys.argv[2] if len(sys.argv) > 2 else 'list'

    if action == 'add':
        # Adicionar uma nota de atualização
        note_text = ' '.join(sys.argv[3:]) if len(sys.argv) > 3 else None
        if not note_text:
            log_error("Uso: python gdrive_sync.py updates add <mensagem>")
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        hostname = os.environ.get('COMPUTERNAME', os.environ.get('HOSTNAME', 'unknown'))
        note_file = GENERAL_UPDATES_DIR / f"update_{timestamp}_{hostname}.md"

        content = (
            f"# Atualização - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"**Computador:** {hostname}\n"
            f"**Usuário:** mauricio.s.lacerda@gmail.com\n\n"
            f"## Nota\n{note_text}\n"
        )

        with open(note_file, 'w', encoding='utf-8') as f:
            f.write(content)
        log_success(f"Nota de atualização criada: {note_file.name}")

    elif action == 'list':
        # Listar atualizações
        if not GENERAL_UPDATES_DIR.exists():
            log("Nenhuma atualização encontrada.")
            return

        updates = sorted(GENERAL_UPDATES_DIR.glob('*.md'), reverse=True)
        if not updates:
            log("Nenhuma atualização encontrada.")
            return

        log(f"📋 {len(updates)} atualização(ões) encontrada(s):\n")
        for u in updates[:10]:  # Mostrar últimas 10
            with open(u, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip().replace('# ', '')
            log(f"  📄 {u.name}: {first_line}")

    elif action == 'clear':
        # Limpar atualizações antigas (> 30 dias)
        if not GENERAL_UPDATES_DIR.exists():
            return
        old_files = []
        cutoff = datetime.now().timestamp() - (30 * 86400)
        for u in GENERAL_UPDATES_DIR.glob('*.md'):
            if u.stat().st_mtime < cutoff:
                old_files.append(u)

        if not old_files:
            log("Nenhuma atualização antiga para limpar.")
            return

        log(f"📋 {len(old_files)} arquivo(s) antigo(s) encontrado(s):")
        for f in old_files:
            log(f"    🗑️  {f.name}")

        if not confirm_action(
            f"Excluir {len(old_files)} atualização(ões) com mais de 30 dias?",
            [f.name for f in old_files]
        ):
            return

        count = 0
        for u in old_files:
            audit.info(f'DELETE update: {u.name}')
            u.unlink()
            count += 1
        log_success(f"{count} atualização(ões) antiga(s) removida(s).")

    else:
        log_error(f"Ação desconhecida: {action}")
        log("Uso: python gdrive_sync.py updates [list|add|clear]")


# ============================================================================
# MAIN
# ============================================================================

COMMANDS = {
    'auth': cmd_auth,
    'push': cmd_push,
    'pull': cmd_pull,
    'sync': cmd_sync,
    'status': cmd_status,
    'updates': cmd_updates,
}


def main():
    # Filtrar flags dos argumentos
    args = [a for a in sys.argv[1:] if not a.startswith('--')]

    if not args or args[0] not in COMMANDS:
        print(__doc__)
        print("Comandos disponíveis:")
        for cmd, func in COMMANDS.items():
            print(f"  {cmd:10s} - {func.__doc__.strip()}")
        print("\nFlags de segurança:")
        print("  --dry-run   Simular sem fazer alterações")
        print("  --yes       Aprovar automaticamente todas as ações")
        sys.exit(1)

    if DRY_RUN:
        log("\n🔍 MODO DRY-RUN ATIVO - nenhuma alteração será feita.\n", Colors.WARNING)

    command = args[0]
    audit.info(f'=== COMANDO: {command} (dry_run={DRY_RUN}, auto_approve={AUTO_APPROVE}) ===')
    COMMANDS[command]()


if __name__ == '__main__':
    main()
