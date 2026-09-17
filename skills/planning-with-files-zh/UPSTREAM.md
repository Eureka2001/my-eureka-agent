# 上游参考与本地维护

本 Skill 由 [OthmanAdi/planning-with-files](https://github.com/OthmanAdi/planning-with-files) 的中文规划模式提炼而来，初始参考版本为 `3.19.0`（2026-09-17）。

本目录是 `my-eureka-agent` 的本地真源，不自动跟随上游更新。升级时请比较上游的中文 Skill、模板和脚本，只选择与本仓库需求相符的改动；不要直接覆盖本地文件。

有意未纳入的上游能力：生命周期 hooks、会话历史回放、停止门禁、完整性证明及跨宿主安装逻辑。这些能力与具体 Agent 宿主和安装路径耦合，应在确有需求时单独设计、测试后再加入。
