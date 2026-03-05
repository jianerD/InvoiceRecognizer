# InvoiceRecognizer 发票识别工具 V2.0

一款功能强大的发票识别与整理工具，支持多种发票类型，采用现代化UI设计，同时提供GUI和CLI两种使用方式。

## 功能特性

### 发票识别
- **火车票** - 自动识别站点、日期、金额
- **滴滴发票** - 电子发票 + 行程报销单（按金额自动配对）
- **餐饮发票** - 识别商家、日期、金额
- **通行发票** - 高速通行费发票
- **机票行程单** - 航空公司行程单识别
- **话费发票** - 移动、联通、电信运营商发票
- **酒店发票** - 酒店住宿发票
- **快递发票丰、中通等快递发票
-** - 顺 **车辆租赁** - 商务租车发票

### 暂存区功能
- 先导入行程发票（火车票、机票）暂存
- 后续补充其他类型发票
- 智能关联同一次出行的发票

### 发票整理
- 按日期区间自动整理
- 滴滴发票自动匹配（电子发票 + 行程报销单）
- 自动生成统计报告

### 统计报告
- 按类型统计发票数量和金额
- 支持导出JSON/Excel格式

## 界面预览

### GUI界面（V2.0 现代化设计）
- 仪表盘：总览发票统计数据
- 发票识别：支持直接识别或导入暂存区
- 暂存区管理：查看和管理暂存发票
- 发票整理：按区间整理和自动匹配
- 统计报告：查看和导出统计数据

### CLI命令行
支持无GUI环境下使用：

```bash
# 识别发票
python -m invoice_cli recognize --input ./invoices --output ./output

# 查看暂存区
python -m invoice_cli staging list

# 添加发票到暂存区
python -m invoice_cli staging add --input ./invoices

# 按区间整理发票
python -m invoice_cli organize range --start 2026-01-01 --end 2026-01-31

# 查看统计报告
python -m invoice_cli report
```

## 安装

### 环境要求
- Python 3.8+

### 安装依赖

```bash
pip install -r requirements.txt
```

主要依赖：
- pdfplumber - PDF文本提取
- pandas - 数据处理和导出
- openpyxl - Excel导出
- pyinstaller - 程序封装
- tkinter - GUI界面（Python自带）

## 封装为exe（可选）

如果需要将程序封装为Windows可执行文件：

```bash
# 安装封装工具
pip install pyinstaller

# 封装GUI程序
pyinstaller --onefile --windowed --name InvoiceRecognizer --add-data "invoice_core;invoice_core" invoice_gui.py
```

封装后的文件位于 `dist/InvoiceRecognizer.exe`

## 使用方法

### 方式一：GUI图形界面

```bash
python invoice_gui.py
```

### 方式二：CLI命令行

```bash
# 识别发票
python -m invoice_cli recognize -i ./data -o ./output

# 查看暂存区
python -m invoice_cli staging list

# 添加发票到暂存区
python -m invoice_cli staging add -i ./data

# 整理发票
python -m invoice_cli organize range --start 2026-01-01 --end 2026-01-31

# 导出报告
python -m invoice_cli report --excel
```

## 项目结构

```
InvoiceRecognizer/
├── invoice_gui.py          # GUI主程序
├── invoice_cli.py           # CLI命令行工具
├── invoice_core/            # 核心模块
│   ├── __init__.py
│   ├── recognizer.py       # 发票识别引擎
│   └── storage.py          # 暂存区管理
├── data/                   # 数据目录
│   ├── staging/           # 暂存区
│   └── processed/          # 已处理发票
├── tests/                  # 测试目录
├── docs/                   # 文档目录
├── requirements.txt
└── README.md
```

## 使用流程

### GUI使用流程

1. **启动程序**
   ```bash
   python invoice_gui.py
   ```

2. **导入行程发票**
   - 进入"暂存区"页面
   - 点击"导入行程发票"
   - 选择包含火车票、机票的目录

3. **补充其他发票**
   - 稍后补充餐饮、滴滴等其他发票
   - 点击"补充其他发票"

4. **整理发票**
   - 进入"发票整理"页面
   - 输入日期区间
   - 点击"开始整理"

5. **查看报告**
   - 进入"统计报告"页面
   - 可导出JSON或Excel

## CLI使用示例

```bash
# 1. 识别发票目录
python -m invoice_cli recognize -i ./invoices -o ./processed

# 2. 将发票添加到暂存区
python -m invoice_cli staging add -i ./invoices

# 3. 查看暂存区内容
python -m invoice_cli staging list

# 4. 按区间整理
python -m invoice_cli organize range --start 2026-01-01 --end 2026-01-31

# 5. 滴滴发票自动匹配
python -m invoice_cli organize match --start 2026-01-01 --end 2026-01-31

# 6. 生成报告
python -m invoice_cli report --excel
```

## 更新日志

### V2.0 (2026-03)
- 新增暂存区功能，支持先导入行程发票再补充其他类型
- 重构GUI界面，采用现代化设计
- 新增CLI命令行工具支持
- 新增话费和酒店发票识别
- 新增快递发票识别
- 新增统计报告导出功能

### V1.0 (初始版本)
- 基础发票识别功能
- 按火车票区间整理发票
- 统计报告生成

## License

MIT License
