# 项目简介

---

## 安装方式

```bash
chmod +x ./install.sh
./install.sh
```

---
## 模块介绍

---
### qdata

#### 类CDataDescriptor

使用该类来提供描述一张表,方便在transmatrix中管理使用.

#### 函数save_df_to_db

将一个pd.Dataframe保存到指定表中.

---
### qwidgets

#### 终端输出渲染

使用SFG/SFR等函数使在终端中输出颜色字体

```python
from qtools_sxzq.qwidgets import SFG

print(f"This output is normal, {SFG('but this output is green')}")
```

---
### qplot

`matplotlib`基础上进一步封装的绘图函数, 在Pycharm/VSCode智能提示加持下, 绘图参数更加清晰.

以下示例

#### 生成数据
```python
import pandas as pd
from random import randint

test_size = 60
data = pd.DataFrame(
    {
        "T": [str(_) for _ in range(2014, 2014 + test_size)],
        "x": [randint(95, 105) for _ in range(test_size)],
        "y": [randint(95, 105) for _ in range(test_size)],
    }
).set_index("T")
```

#### 绘图
```python
from qtools_sxzq.qplot import CPlotLines

my_artist = CPlotLines(
    plot_data=data,
    fig_name="test-qplot-lines",  # 保存图片文件名
    fig_save_dir=r"/tmp",  # 保存位置
    line_width=4,  # 线条宽度
    line_style=["-", "-."],  # 线条样式
    line_color=["#DC143C", "#228B22"],  # 线条颜色,可以用utility.view_colors查看更多颜色
)
my_artist.plot()
my_artist.set_legend(size=16, loc="upper left")  # 设置图例
my_artist.set_axis_x(  # 设置x轴
    xtick_count=10,  # x轴标签数量
    # xtick_spread=20, # x轴标签间距,与数量不要同时设置
    xlabel="Test-XLabels",  # x轴标签
    xtick_label_size=24,  # x轴刻度标签大小
    xtick_label_rotation=45,  # x轴刻度标签旋转角度
)
my_artist.set_title(title="test-qplot-lines", size=48, loc="left")
my_artist.save_and_close()
```

**绘图时请确认data是pd.DataFrame, 且索引index是字符串格式，否则set_axis_x()函数可能不会正常运行**

---
### utility.ls_tqdb

展示数据库中所有可用表.

```bash
python -m qtools_sxzq.utility.ls_tqdb --lib huxiaoou_private
```

---
### utility.rm_tqdb

删除数据库中指定表

```bash
python -m qtools_sxzq.utility.rm_tqdb --lib huxiaoou_private --table name_of_table_to_remove
```

删除数据库中所有表

```bash
python -m qtools_sxzq.utility.rm_tqdb --lib huxiaoou_private -r
```

---
### utility.view_tqdb

使用view_tqdb在终端中快速查看数据库.

#### 查看帮助

```bash
 python -m qtools_sxzq.utility.view_tqdb -h
```

输出

```bash
usage: view_tqdb.py [-h] --lib LIB --table TABLE [--vars VARS] [--where WHERE] [--head HEAD] [--tail TAIL] [--maxrows MAXROWS]

A python script to view trans-quant database

optional arguments:
  -h, --help         show this help message and exit
  --lib LIB          path for trans-quant database, like 'huxiaoou_private' or 'meta_data'
  --table TABLE      table name in the database, like 'table_avlb' or 'future_bar_1day'
  --vars VARS        variables to fetch, separated by ',' like "open,high,low,close", if not provided then fetch all.
  --where WHERE      conditions to filter, sql expressions like "code = 'A9999_DCE'" AND datetime >= '2024-10-01 09:00:00'
  --head HEAD        integer, head lines to print
  --tail TAIL        integer, tail lines to print
  --maxrows MAXROWS  integer, provide larger value to see more rows when print outcomes
```

#### 查看数据库`meta_data`中的表`future_bar_1day`

```bash
python -m qtools_sxzq.utility.view_tqdb --lib meta_data --table future_bar_1day --vars 'code,trade_day,`open`,high,low,`close`'
```

输出结果

```bash
SELECT code,trade_day,`open`,high,low,`close` FROM future_bar_1day:
             code   trade_day         open         high          low        close
0       A2005_DCE  2020-01-02  2522.345237  2535.427940  2516.458020  2525.615913
1       A2005_DCE  2020-01-03  2525.615913  2546.548238  2524.961778  2536.082076
2       A2005_DCE  2020-01-06  2533.465535  2558.322672  2527.578318  2557.014401
3       A2005_DCE  2020-01-07  2560.939212  2579.254997  2555.051996  2561.593347
4       A2005_DCE  2020-01-08  2561.593347  2593.645971  2555.706131  2586.450484
...           ...         ...          ...          ...          ...          ...
251716  Y2105_DCE  2021-04-02  5855.125676  5890.446620  5746.445849  5882.295633
251717  Y2105_DCE  2021-04-06  5864.635161  6020.862412  5864.635161  5980.107477
251718  Y2105_DCE  2021-04-07  6009.994429  6087.428806  5984.182970  6000.484944
251719  Y2105_DCE  2021-04-08  6000.484944  6024.937906  5845.616191  5867.352157
251720  Y2105_DCE  2021-04-09  5876.861641  5939.352542  5834.748208  5849.691685
```

注意,由于`open`和`close`两个价格和数据库中保留关键字重复,需要使用"`"符号包围起来.

---
### utility.view_colors

查看各项颜色代码

```bash
python -m qtools_sxzq.utility.view_colors
```