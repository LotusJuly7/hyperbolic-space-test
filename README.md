# PyOpenGL 双曲空间示例

这个示例使用 **PyOpenGL + pygame** 渲染一个 3D 双曲空间（Poincaré ball 模型）：

- 场景里有少量小块多面体（四面体、立方体、八面体）。
- 视角支持前后移动、左右转向。
- 摄像机固定在原点，作为第一人称视角；前后移动通过对所有物体中心做 Möbius 变换实现。
- 渲染时所有物体都映射在单位球体内。

## 运行

```bash
pip install pygame PyOpenGL
python hyperbolic_scene.py
```

## 操作

- `W/S` 或 `↑/↓`：前后移动（通过 Möbius 变换移动世界）
- `A/D` 或 `←/→`：左右转向（仅改变第一人称朝向，不再额外旋转整个世界）
- 关闭窗口退出
