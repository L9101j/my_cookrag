CREATE TABLE recipes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL UNIQUE,           -- 菜名
    category VARCHAR(50) NOT NULL,               -- 分类
    difficulty ENUM('easy','medium','hard'),     -- 难度
    content TEXT NOT NULL,                       -- 完整的 Markdown 内容
    file_path VARCHAR(500),                      -- 原始文件路径
    parent_id VARCHAR(100) UNIQUE,               -- 对应 document_processor 的 parent_id
    INDEX idx_category (category),
    INDEX idx_difficulty (difficulty),
    INDEX idx_parent_id (parent_id)
);

CREATE TABLE chat_messages (
    id INT PRIMARY KEY AUTO_INCREMENT,          
    session_id VARCHAR(100) NOT NULL,            -- 会话ID（格式：user_id_YYYYMMDD）
    message_id INT NOT NULL,                     -- 消息ID（同一session内的消息序号，从1开始）
    role ENUM('user', 'assistant', 'system'),    -- 角色
    content TEXT NOT NULL,                       -- 消息内容
    intent VARCHAR(50),                          -- 意图（list/detail/general）
    rewrited_query TEXT,                         -- 重写后的查询
    sources JSON,                                -- 引用的菜谱来源
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session (session_id),
    INDEX idx_session_message (session_id, message_id),
    INDEX idx_created_at (created_at)
);

CREATE TABLE document_chunks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    chunk_id VARCHAR(100) NOT NULL UNIQUE,       -- 对应 document_processor 的 chunk_id
    parent_id VARCHAR(100) NOT NULL,             -- 所属父文档
    content TEXT NOT NULL,                       -- 块内容
    chunk_index INT,                             -- 在父文档中的序号                       -- Markdown 标题层级
    FOREIGN KEY (parent_id) REFERENCES recipes(parent_id),
    INDEX idx_parent (parent_id),
    INDEX idx_chunk_id (chunk_id)
);


