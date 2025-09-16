
```markdown
# Backtrader + Baostock 分钟线可视化脚本

## 功能说明
- 从Baostock获取股票/基金分钟线数据（1m/5m）
- 使用Backtrader进行技术指标绘制和可视化
- 支持交互式图表（Bokeh）或Matplotlib输出
- 自动处理交易日范围和数据清洗

## 用户参数配置
```python
# 修改以下参数即可使用
SYMBOL = 'sh.601012'        # 股票代码（sh./sz.前缀）
FREQ   = '5'                # 分钟粒度（'1'/'5'）
DAYS   = 5                  # 最近N个交易日
ADJ    = '3'                # 复权方式：'1'=后复权/'2'=前复权/'3'=不复权
USE_BOKEH = True            # 是否使用交互式图表
TITLE  = f'{SYMBOL} 近{DAYS}个交易日 {FREQ}分钟'  # 图表标题
```

## 依赖库安装

```bash
pip install baostock backtrader pandas numpy
pip install backtrader_plotting  # 如果使用Bokeh交互式图表
```

## 代码结构解析

### 1. 数据获取模块

```python
def fetch_baostock_minute_df()
```

- 通过Baostock API获取分钟线数据
- 返回标准化DataFrame（含datetime索引）
- 包含字段：open/high/low/close/volume/openinterest
- 自动处理数据类型转换和缺失值

### 2. 交易日计算

```python
def get_last_n_trade_day_range(n=5)
```

- 计算最近N个交易日的时间范围
- 向后多给20天缓冲以覆盖节假日

### 3. Backtrader策略

```python
class ShowOnly(bt.Strategy):
    def __init__(self):
        self.sma_fast = bt.ind.SMA(self.data.close, period=20)
        self.sma_slow = bt.ind.SMA(self.data.close, period=60)
        self.macd = bt.ind.MACD(...)
```

- 添加技术指标用于可视化展示
- 当前为纯展示模式（无实际交易逻辑）

### 4. 主流程执行

```python
def run():
    # 获取数据
    df = fetch_baostock_minute_df(...)
  
    # 数据筛选
    dates = pd.Index(df.index.date).unique()
    df = df[df.index.date.astype('O').isin(last_n)]
  
    # Backtrader配置
    cerebro = bt.Cerebro()
    data = bt.feeds.PandasData(...)
  
    # 绘图处理
    if USE_BOKEH:
        from backtrader_plotting import Bokeh
        cerebro.plot(b)
    else:
        cerebro.plot(style='candle')
```

## 使用说明

1. **注册Baostock账户**

   - 访问 https://www.baostock.com/
   - 注册开发者账号并获取API权限
2. **运行脚本**

   ```bash
   python script_name.py
   ```
3. **输出结果**

   - 默认打开交互式图表（Bokeh）
   - 或保存为HTML文件（bt_plot.html）
   - Matplotlib模式显示蜡烛图+成交量

## 注意事项

- Baostock每日免费请求次数限制
- 确保网络连接稳定（API请求需联网）
- 时间范围设置过大可能导致数据量爆炸增长
- 交互式图表需要浏览器支持JavaScript

## 技术指标扩展

可在 `ShowOnly`类中添加更多指标：

```python
# 示例：添加RSI指标
self.rsi = bt.ind.RSI(self.data.close, period=14)
# 示例：布林带
self.bband = bt.ind.BBands(self.data.close, period=20)
```

## 常见问题

Q: 出现Baostock登录失败？
A: 检查网络连接或联系Baostock获取API权限

Q: 数据获取为空？
A: 检查股票代码格式（sh.600000）、时间范围或尝试修改复权参数

Q: Bokeh绘图失败？
A: 安装 `backtrader_plotting`包或改用Matplotlib模式
