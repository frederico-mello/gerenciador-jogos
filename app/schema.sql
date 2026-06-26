-- Schema do banco de jogos
-- NOSONAR: plsql:S1192 — DEFAULT datetime expression is a SQLite requirement; duplication across columns is intentional

CREATE TABLE IF NOT EXISTS games (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    nome               TEXT NOT NULL,
    area               TEXT NOT NULL CHECK (area IN ('anatomia', 'histologia', 'microbiologia')),
    descricao          TEXT,
    regras_resumo      TEXT,
    num_jogadores      TEXT,
    duracao_min        INTEGER,
    imagem_componentes TEXT,
    imagem_perfil      TEXT,
    created_at         TEXT DEFAULT (datetime('now', 'localtime')),
    updated_at         TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS game_manual_pages (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    ordem   INTEGER NOT NULL,
    path    TEXT NOT NULL,
    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_games_area ON games(area);
CREATE INDEX IF NOT EXISTS idx_manual_game ON game_manual_pages(game_id);

CREATE TABLE IF NOT EXISTS schools (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_inep  TEXT UNIQUE,
    nome         TEXT NOT NULL,
    rede         TEXT CHECK(rede IN ('federal','estadual','municipal','privada')),
    endereco     TEXT,
    bairro       TEXT,
    cep          TEXT,
    ativo        INTEGER DEFAULT 1,
    created_at   TEXT DEFAULT (datetime('now', 'localtime')),
    updated_at   TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_schools_rede ON schools(rede);
CREATE INDEX IF NOT EXISTS idx_schools_ativo ON schools(ativo);

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nome          TEXT NOT NULL,
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL CHECK(role IN ('admin_sistema','admin_jogos','usuario')),
    escola_id     INTEGER,
    ativo         INTEGER DEFAULT 1,
    receber_emails INTEGER DEFAULT 0,
    created_at    TEXT DEFAULT (datetime('now', 'localtime')),
    updated_at    TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (escola_id) REFERENCES schools(id)
);

CREATE INDEX IF NOT EXISTS idx_users_escola ON users(escola_id);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_ativo ON users(ativo);

CREATE TABLE IF NOT EXISTS loans (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id               INTEGER NOT NULL,
    user_id               INTEGER NOT NULL,
    status                TEXT NOT NULL CHECK(status IN ('solicitado','reservado','emprestado','devolvido','cancelado')),
    devolucao_prevista    DATE,
    renovacao_pendente    INTEGER DEFAULT 0,
    nova_devolucao_prevista DATE,
    observacoes           TEXT,
    solicitado_at         TEXT,
    reservado_at          TEXT,
    emprestado_at         TEXT,
    devolvido_at          TEXT,
    created_at            TEXT DEFAULT (datetime('now','localtime')),
    updated_at            TEXT DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (game_id) REFERENCES games(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_loans_game ON loans(game_id);
CREATE INDEX IF NOT EXISTS idx_loans_user ON loans(user_id);
CREATE INDEX IF NOT EXISTS idx_loans_status ON loans(status);

CREATE TABLE IF NOT EXISTS loan_status_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id         INTEGER NOT NULL,
    status_anterior TEXT,
    status_novo     TEXT NOT NULL,
    changed_by      INTEGER NOT NULL,
    changed_at      TEXT DEFAULT (datetime('now','localtime')),
    observacao      TEXT,
    FOREIGN KEY (loan_id) REFERENCES loans(id) ON DELETE CASCADE,
    FOREIGN KEY (changed_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_history_loan ON loan_status_history(loan_id);

CREATE TABLE IF NOT EXISTS reservation_queue (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id    INTEGER NOT NULL REFERENCES games(id),
    user_id    INTEGER NOT NULL REFERENCES users(id),
    posicao    INTEGER NOT NULL,
    status     TEXT NOT NULL DEFAULT 'na_fila' CHECK(status IN ('na_fila','notificado','atendido','cancelado')),
    created_at TEXT DEFAULT (datetime('now','localtime')),
    updated_at TEXT DEFAULT (datetime('now','localtime'))
);

CREATE INDEX IF NOT EXISTS idx_queue_game ON reservation_queue(game_id);
