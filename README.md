# HAM 通联日志生成器

本项目是一个简单、高效的通联日志自动生成器，适用于业余无线电爱好者（HAM）分享个人 QSO 记录。使用 CSV 数据和 JSON 配置，生成结构化的 HTML 页面，支持部署到 GitHub Pages 或 Cloudflare Pages。

点击 Use this template 创建你的个人 HAM 日志仓库

---

## 项目结构说明

| 文件/目录                     | 说明                                                   |
| ------------------------- | ---------------------------------------------------- |
| `generate_contact_log.py` | 主脚本。读取 `data.csv` 和 `config.json`，生成 `index.html` 页面 |
| `data.csv`                | 通联日志数据，支持中文字段                                        |
| `config.json`             | 个人资料配置，如呼号、证书等级、QTH 等                                |
| `index.html`              | 自动生成的静态页面，可发布在 Pages 上                               |
| `.github/workflows/`      | GitHub Actions CI 自动生成并提交 HTML 的流程定义                 |
| `README.md`               | 本说明文档                                                |

---

## 数据格式说明：`data.csv`

CSV 文件列模板如下，可自定义：

```csv
日期DATE,时间TIME,呼号CALLSIGN,频率,模式MODE,Sent RST,Received RST,Sent PWR,Received PWR,QTH,设备RIG,天线ANT,Notes
2024/10/5,20:57,BD4UOG,430.61,FM,59,59,5W,25W,南京市方山,森海克斯8800,RH-770,
```

## 自定义个人资料块：config.json
可自由添加和变更条目，添加模板之外的条目需自行修改脚本
```json
{
  "callsign": "BD4UOG",
  "license": "B类",
  "operator": "Chantico's Fire",
  "location": "City",
  "grid": "XXXXxx",
  "email": "example@github.com"
}
```
### 署名信息
生成的页面底部会自动显示如下署名信息：
`Copyright © 2025 中国业余无线电台 <你的呼号>`

`<你的呼号>` 字段来自 `config.json` 文件，其他用户使用本模板时可通过修改该配置文件自动生成属于自己的署名信息。


## 使用方法（本地）

```bash
python3 generate_contact_log.py --csv data.csv --config config.json --output index.html
```

## GitHub Actions 自动化构建

项目可配置 GitHub Actions，当你修改 `data.csv`、`config.json` 或 `generate_contact_log.py` 后，会自动：

运行脚本生成 `index.html`

将其提交回仓库

编辑 README.md 不会触发自动构建。

##  欢迎 Fork 与使用

欢迎各位 HAM 同好 Fork 本项目，记录和展示自己的通联日志。

Powered by HAM Log Generator (Template by BD4UOG)
