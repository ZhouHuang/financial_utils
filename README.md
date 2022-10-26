### Pachake import

### 数据导入

### 数据处理

#### 原始因子生成

##### 测试因子

未来一天的收益率

##### 个股超额收益率

1日动量，5日动量，10日动量

##### [振幅因子](https://zhuanlan.zhihu.com/p/156851121)

回看20个交易日

- 每日振幅因子：R = high / low - 1


- 高价振幅因子：V$_{\rm high}(\lambda)$


- 理想振幅因子：V$(\lambda)$ = V$_{\rm high}(\lambda)$ - V$_{\rm low}(\lambda)$


##### 101Alpha

- Alpha$_{4}$: -1 * ts_Rank(rank(low), 9)


- Alpha$_{5}$: (rank((open - (sum(vwap, 10) / 10))) * (-1 * abs(rank((close - vwap)))))


- Alpha$_{25}$: (((-1 $\times$ returns) $\times$ adv20) $\times$ vwap ) $\times$ (high - close)

    较好的负向指标


- Alpha$_{40}$: (-1 $\times$ rank(stddev(high, 10))) $\times$ correlation(high, volume, 10)


- Alpha$_{41}$: ((high $\times$ low)$^{0.5}$) - vwap


- Alpha$_{42}$: (rank ((vwap - close)) / rank ((vwap + close)))
    
    vwap是使用成交量赋权的日内成交价格，在这里我们使用成交额/成交量(Total_turnover / Volume)来代替。
    
    
- Alpha$_{43}$: (ts_rank((volume / adv20), 20) $\times$ ts_rank((-1 $\times$ delta(close, 7)), 8))

#### 空缺值填充

#### 去极值

#### 标准化

#### 中性化

对数市值，行业（申万一级行业，中信一级行业）

### 模型训练

训练集，测试集，验证集

### 回测

回测开始日期：20xx-xx-xx

回测结束日期：20xx-xx-xx

当天交易结束，获得HOLC数据，确定下个交易日的投资标的。第二天以开盘价买入卖出。

### 结果分析

#### 换手率

#### 每日盈亏

#### 每周胜率

#### 因子合成

#### 因子分解
