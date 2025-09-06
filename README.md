# FloatNote API

一个基于Django和MongoDB的现代化信息分类API。

## 项目概述

FloatNote API提供了多业务类型的数据记录，如账单、日程、联系人、笔记、任务等,根据业务的具体类型，自由定义所需的结构化数据，服务就可以根据输入的信息（文本内容、图片、语音），完成结构化数据的提取。


FloatNote API的主要功能包括：
- 多类型数据记录的创建、读取、更新和删除（CRUD）操作
- 用户认证和授权
- 数据处理和转换
- 系统配置和扩展

提供完整的CRUD操作、用户认证和数据处理功能。系统采用RESTful设计风格，集成了Redis缓存、Celery任务队列和LLM处理能力，为前端应用提供稳定高效的数据服务。

## 技术栈

### 核心框架
- **Django 4.2.7** - Web应用框架
- **Django REST Framework 3.16.0** - RESTful API开发框架
- **MongoEngine 0.29.1** - MongoDB ORM

### 数据存储
- **MongoDB** - 主要数据存储
- **Redis 6.2.0** - 缓存和Celery消息代理
- **SQLite** - 部分配置存储（通过dummy引擎兼容Django核心功能）

### 认证与安全
- **JWT (JSON Web Token)** - 用户认证
- **自定义权限系统** - 基于路径的公共/私有访问控制

### API文档与工具
- **drf-spectacular 0.28.0** - OpenAPI 3.0文档生成器


### 任务处理
- **Celery 5.4.0** - 分布式任务队列

### 其他依赖
- **django-cors-headers 4.7.0** - 跨域资源共享支持
- **python-dotenv 1.1.1** - 环境变量管理
- **django-redis 6.0.0** - Django Redis集成

## 项目结构

```
float_note_api/
├── accounts/          # 用户认证与管理模块
├── common/            # 通用组件与工具
├── records/           # 核心记录管理模块
│   ├── cache/         # 缓存相关工具与逻辑
│   ├── llm_processor/ # LLM处理模块
│   ├── models/        # 数据模型定义
│   ├── processor/     # 各类数据处理器
│   ├── services/      # 业务逻辑层
│   ├── utils/         # 工具函数与助手
├── sovo/              # 主项目配置
│   ├── settings.py    # 项目全局配置
│   └── celery.py      # Celery配置
├── requirements.txt   # 项目依赖
└── manage.py          # Django管理脚本
```

## LLM实现的多模态信息分类与自定义结构化数据Schema

### 核心设计思路

项目通过LLM技术实现了灵活的多模态信息分类和自定义结构化数据提取，保证了信息分类的灵活性并实现了数据模型与业务的解耦。

### 多模态信息处理

项目实现了完整的多模态输入处理流程，支持文本、图像和音频等多种输入形式：

1. **多模态预处理器** (`MultiModalPreprocessor`)
   - 支持从图像中提取文本（OCR），使用RapidOCR库进行本地处理
   - 支持从音频中提取文本（ASR），使用faster-whisper-small模型进行语音识别
   - 集成中文繁简转换，确保文本处理的一致性
   - 通过重试机制提高处理可靠性

2. **统一的文本预处理**
   - 将不同类型的输入统一转换为文本格式
   - 为不同来源的内容添加标识，便于后续处理

### 动态类型检测与分类

项目实现了智能的记录类型检测和分类机制：

1. **LLM驱动的类型检测**
   - 使用大语言模型（默认配置为deepseek-chat）进行精确的类型检测
   - 支持根据预定义的类型列表进行分类
   - 提供类型检测失败时的备选方案

2. **可配置的类型定义**
   - 通过`RecordType`枚举定义支持的记录类型（账单、日程、联系人、笔记、任务、支出等）
   - 支持根据业务需求扩展新的记录类型

### 自定义结构化数据Schema

项目实现了灵活的自定义结构化数据schema机制，实现数据模型与业务逻辑的解耦：

1. **基于Pydantic的Schema定义**
   - 为每种记录类型定义专用的Schema类（如`BillSchema`、`ScheduleSchema`等）
   - 明确字段类型、描述、默认值和验证规则
   - 通过`SCHEMA_MAPPING`实现类型与Schema的动态映射

2. **动态字段规范**
   - 通过`FieldSpec`嵌入式文档定义动态字段规范
   - 支持多种数据类型（string、number、boolean、date、array、reference）
   - 支持字段必填性、默认值、引用模型、描述和枚举值等配置

3. **灵活的字段扩展**
   - 允许通过配置动态扩展记录类型的字段
   - 支持用户自定义字段，满足个性化需求

### 信息提取与标签生成

项目实现了基于LLM的智能信息提取和标签生成功能：

1. **结构化信息提取**
   - 根据检测到的记录类型，自动选择对应的Schema进行信息提取
   - 支持从非结构化文本中提取结构化数据
   - 处理缺失信息，确保数据完整性

2. **智能标签管理**
   - 支持从提取结果中自动生成相关标签
   - 结合用户已有标签进行推荐
   - 区分系统生成标签和用户自定义标签

### 系统优势

1. **高度灵活性**
   - 通过配置而非硬编码支持多种记录类型
   - 支持动态扩展字段和类型
   - 适应不同业务场景的需求变化

2. **数据模型与业务解耦**
   - Schema定义与业务逻辑分离
   - 支持运行时动态加载和配置Schema
   - 便于维护和扩展

3. **多模态支持**
   - 统一处理不同类型的输入
   - 本地模型处理，保证数据隐私
   - 高效的文本提取和转换

通过这种设计，项目能够灵活应对不同类型的信息处理需求，实现高度可配置和可扩展的信息分类与结构化提取系统。

## 快速开始

### 环境准备

1. **安装Python 3.11+**
2. **安装MongoDB 4.4+**
3. **安装Redis 6.0+**

### 安装步骤

1. **克隆项目**

```bash
# 克隆项目到本地
cd /path/to/your/workspace
git clone <repository-url>
cd tutorial
```

2. **创建虚拟环境**

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
source venv/bin/activate
# macOS/Linux
. venv/bin/activate
```

3. **安装依赖**

```bash
pip install -r requirements.txt
```

4. **配置环境变量**

创建`.env`文件并配置必要的环境变量：

```env
# MongoDB配置
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DB=sovo
MONGODB_USERNAME=admin
MONGODB_PASSWORD=admin

OPENAI_API_KEY="deepseek api key"
OPENAI_API_BASE=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
DEFAULT_MAX_TOKENS=1500

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379

# 项目密钥
SECRET_KEY=django-insecure-@n8y2kp0+las7ax^y0^n*%c15!v_8r*ce6)c)97_at35*8ej@1

# 调试模式
DEBUG=True
```

5. **启动开发服务器**

```bash
python manage.py runserver
```

6. **启动Celery工作器（可选，用于异步任务）**

```bash
celery -A sovo worker --loglevel=info

# 启动Celery Beat（用于定时任务）
celery -A sovo beat --loglevel=info
```

## API文档

项目集成了完整的API文档系统，启动服务器后可通过以下地址访问：

- **OpenAPI 3.0文档**：`http://localhost:8000/api/schema/swagger-ui/`
- **Swagger 2.0文档**：`http://localhost:8000/api/docs/`

## 核心功能模块

### 用户管理 (accounts)
- 用户注册、登录与认证
- JWT令牌管理
- 权限控制

### 记录管理 (records)
- 支持多种记录类型：账单、日程、联系人、笔记、任务等
- 记录的创建、查询、更新和删除
- 使用Redis缓存优化查询性能
- 支持文件上传和处理
- 集成LLM处理能力

### 数据处理与分类
- 自动分类识别
- 文本、音频、图像处理
- 动态表单和字段规范

### 缓存系统
- 基于Redis的高性能缓存
- 支持自动回源和反序列化处理
- 容错机制确保系统稳定性

## 开发指南
- 项目进行中...

### 运行测试

```bash
python manage.py test
```

### 代码规范

项目遵循Django和Python的最佳实践，建议使用以下工具进行代码检查：

- **flake8**：代码风格检查
- **black**：代码格式化
- **isort**：导入语句排序

## Docker部署

项目提供了Docker支持，可通过以下步骤部署：

1. **构建镜像**

```bash
docker build -t float_note-api .
```

2. **使用Docker Compose启动**

```bash
docker-compose up -d
```

## 注意事项

1. **开发环境与生产环境**
   - 开发环境使用`.env`文件
   - 生产环境使用`.env.docker`文件（自动加载）

2. **缓存问题处理**
   - 系统实现了完整的缓存容错机制
   - 在缓存数据格式不兼容时会自动回源获取
   - 支持缓存键自动生成和管理

3. **MongoDB连接**
   - 配置文件中已设置连接池大小和超时时间
   - 支持TLS加密连接（需配置证书）

## 许可证

[MIT License](LICENSE)

## 贡献指南

1. Fork项目仓库
2. 创建功能分支
3. 提交代码变更
4. 创建Pull Request

## 联系方式

如有问题或建议，请联系项目维护人员。