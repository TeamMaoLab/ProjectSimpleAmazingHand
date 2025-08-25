# 使用 micropython 快速实现一个单手指控制的网页demo

## 目标

通过 ESP32 和 micropython，实现一个可以通过网页控制单个手指开合的 demo。该项目包含多个阶段，从基础的舵机控制到完整的网页交互。

## 物料信息

### 舵机 (SG90/SG92 或 360度连续旋转舵机)

- **型号**: SG90, SG92 或兼容的 360 度连续旋转舵机
- **引脚定义**:
  - 棕色: GND
  - 红色: +5V
  - 橘黄色: PWM 信号线 (连接到 ESP32 的 D13)
- **类型**: 
  - **标准舵机 (SG90/SG92)**: 可通过 PWM 信号控制在 0-180 度范围内精确定位。
  - **360度连续旋转舵机**: 通过 PWM 信号控制旋转速度和方向，无绝对位置反馈。
- **控制方式**: 
  - 底层通过 PWM 信号控制。
  - 对于标准舵机，可以通过角度函数进行控制。
  - 对于 360 度舵机，PWM 信号决定旋转速度和方向：
    - **~1.5ms 脉冲 (约 duty 75)**: 停止。
    - **< 1.5ms 脉冲 (约 duty 25-70)**: 以不同速度顺时针旋转。
    - **> 1.5ms 脉冲 (约 duty 80-125)**: 以不同速度逆时针旋转。
  - 当前代码实现了对两种舵机类型的直接 PWM 控制，便于测试和校准。

## 阶段一：基础舵机控制与测试

### 目标
验证舵机硬件连接，并实现基础的 PWM 控制功能。

### 步骤
1.  准备 ESP32 开发板和舵机。
2.  将 MicroPython 固件刷入 ESP32 DevKit V1。
3.  编写并上传基础的舵机测试脚本 (`servo_test.py`)。
4.  通过串口终端手动测试舵机在不同 PWM 值下的响应。

### 相关文件
- 代码: `archive/DT250823_esp32_web_control_demo/servo_test.py`

## 阶段二：集成 Web 服务器的初步控制

### 目标
实现一个简单的 Web 服务器，可以通过网页按钮控制舵机的基本开合动作或旋转方向。

### 步骤
1.  在 ESP32 上实现 Web 服务器。
2.  创建一个包含“Open”和“Close”按钮的简单网页。
3.  实现服务器端逻辑，根据按钮点击控制舵机。
4.  (针对360度舵机) 增加直接 PWM 调节功能，用于测试和校准。

### 相关文件
- 代码: `archive/DT250823_esp32_web_control_demo/esp32_web_control_demo.py` (旧版，已归档)
- 代码: `esp32_web_control_demo.py` (当前版本)

## 阶段三：前后端分离与 API 设计

### 目标
将 Web 服务器的后端逻辑与前端页面完全分离，设计清晰的 RESTful API，为更复杂的控制和交互提供基础。

### 步骤
1.  设计并实现专门的 Web API 服务器 (`servo_api_server.py`)。
2.  定义 API 接口，支持获取状态、执行单步旋转等操作。
3.  创建独立的 HTML 前端页面，通过 AJAX 调用后端 API。
4.  实现针对 360 度舵机的“点动”控制功能（点击一次，旋转一小步）。

### 相关文件
- 后端代码: `servo_api_server.py`
- 后端文档: `docs/plans/esp32_360_servo_api.md`
- 前端页面: (待创建)

## 状态

进行中

## 完成日期

(未完成)

### ESP32 开发板

- **型号**: ESP32 DevKit V1

## 步骤

1.  准备 ESP32 开发板和舵机。
2.  将 MicroPython 固件刷入 ESP32 DevKit V1。
3.  编写 micropython 代码，通过 PWM 控制舵机。
    -   代码文件: `../archive/DT250823_esp32_web_control_demo/esp32_web_control_demo.py`
    -   舵机连接到 GPIO 14。
    -   实现了 `set_servo_angle` 函数来控制角度。
4.  实现一个简单的 Web 服务器，提供网页界面。
    -   代码文件: `../archive/DT250823_esp32_web_control_demo/esp32_web_control_demo.py`
    -   服务器监听 80 端口。
    -   提供一个 HTML 页面用于控制和状态显示。
5.  在网页上添加按钮，控制手指的开合。
    -   代码文件: `../archive/DT250823_esp32_web_control_demo/esp32_web_control_demo.py`
    -   "Open Finger" 按钮发送 `/open` 请求。
    -   "Close Finger" 按钮发送 `/close` 请求。
    -   服务器根据请求调用 `set_servo_angle` 控制舵机。
6.  增强网页交互性，实现实时状态反馈。
    -   代码文件: `../archive/DT250823_esp32_web_control_demo/esp32_web_control_demo.py`
    -   使用 JavaScript (AJAX) 发送异步请求，避免页面刷新。
    -   服务器直接返回状态字符串，前端动态更新状态显示区域。
    -   为不同状态添加了颜色编码（绿色 Open, 红色 Closed）。
7.  为 Web 服务器配置本地域名 (mDNS)。
    -   代码文件: `../archive/DT250823_esp32_web_control_demo/esp32_web_control_demo.py`
    -   尝试使用 `mdns` 模块注册服务 `esp32demo`。
    -   成功后可通过 `http://esp32demo.local` 访问 (取决于固件支持)。
8.  测试并优化。

## 状态

已完成

## 完成日期

2025-08-23