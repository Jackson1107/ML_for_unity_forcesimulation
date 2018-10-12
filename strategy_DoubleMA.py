# -*- coding: utf-8 -*-
"""
@Date   : 2018/10/10 13:48
@Author : Jack
@Content: 双均线测试策略1
"""
import talib
import numpy as np

from vnpy.trader.app.ctaStrategy.ctaBase import *
from vnpy.trader.app.ctaStrategy.ctaTemplate import CtaTemplate


########################################################################
class DoubleMA1Strategy(CtaTemplate):
    """双均线测试策略1"""
    # ----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """构造器"""
        super(DoubleMA1Strategy, self).__init__(ctaEngine, setting)
        # 策略信息
        self.className = 'DoubleMA1Strategy'
        self.author = "Jack"
        self.name = "Strategy_DoubleMA"

        # 策略参数
        self.n1 = setting["ma1"]           # 短期均线参数
        self.n2 = setting["ma2"]           # 长期均线参数
        self.fixedSize = setting["fixedSize"] # 每次开仓手数

        # K线储存变量
        self.num_k = self.n2                 # K线储存个数
        self.closeArr = np.zeros(self.num_k) # 收盘价缓存序列
        self.count_k = 0                     # 当前K线的序号

        # 指标变量
        self.ma1 = np.nan                   # 短期均线值
        self.ma2 = np.nan                   # 长期均线值

        # 其他变量
        self.orderList = []  # 保存委托代码的列表

        # 参数列表，保存了参数的名称(实盘用)
        self.paramList = ['name',
                          'className',
                          'author',
                          'vtSymbol']

        # 变量列表，保存了变量的名称(实盘用)
        self.varList = ['inited',
                        'trading',
                        'pos']

    # ----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略初始化' % self.name)

        # 载入历史数据，并采用回放计算的方式初始化策略数值
        initData = self.loadBar()
        for bar in initData:
            self.onBar(bar)
        self.putEvent()

    # ----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略启动' % self.name)
        self.putEvent()

    # ----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略停止' % self.name)
        self.putEvent()

    # ----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        # 计算K线
        tickMinute = tick.datetime.minute

        if tickMinute != self.barMinute:
            if self.bar:
                self.onBar(self.bar)

            bar = CtaBarData()
            bar.vtSymbol = tick.vtSymbol
            bar.symbol = tick.symbol
            bar.exchange = tick.exchange

            bar.open = tick.lastPrice
            bar.high = tick.lastPrice
            bar.low = tick.lastPrice
            bar.close = tick.lastPrice

            bar.date = tick.date
            bar.time = tick.time
            bar.datetime = tick.datetime  # K线的时间设为第一个Tick的时间

            self.bar = bar  # 这种写法为了减少一层访问，加快速度
            self.barMinute = tickMinute  # 更新当前的分钟
        else:  # 否则继续累加新的K线
            bar = self.bar  # 写法同样为了加快速度

            bar.high = max(bar.high, tick.lastPrice)
            bar.low = min(bar.low, tick.lastPrice)
            bar.close = tick.lastPrice

    # ----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        # 收到新的K线后，撤销之前所有的限价单和停止单
        for orderID in self.orderList:
            self.cancelOrder(orderID)
        self.orderList = []

        # 保存K线数据
        self.closeArr[0:self.num_k-1] = self.closeArr[1:self.num_k]
        self.closeArr[-1] = bar.close

        # 更新K线数量
        self.count_k += 1

        # 排除数据不足的情况
        if self.count_k < self.num_k:
            return

        # 计算均线指标
        self.ma1 = self.closeArr[-self.n1:].mean()
        self.ma2 = self.closeArr[-self.n2:].mean()

        # -------------------------------------------------------------
        # 信号部分
        trend_up = self.ma1 > self.ma2   # 趋势向上
        trend_dn = self.ma1 < self.ma2   # 趋势向下

        # -------------------------------------------------------------
        # 交易判断部分
        # 当前无仓位
        if self.pos == 0:
            # 短期均线在长期均线上方，开多
            if trend_up:
                # 这里为了保证成交，选择超价5个整指数点下单
                self.buy(bar.close + 5, self.fixedSize)
            # 短期均线在长期均线上方，开空
            elif trend_dn:
                # 这里为了保证成交，选择超价5个整指数点下单
                self.short(bar.close - 5, self.fixedSize)

        # 持有多头仓位
        elif self.pos > 0:
            # 趋势转空，平多开空
            if trend_dn:
                self.sell(bar.close - 5, abs(self.pos))
                self.short(bar.close - 5, self.fixedSize)

        # 持有空头仓位
        elif self.pos < 0:
            # 趋势转多，平空开多
            if trend_up:
                self.cover(bar.close + 5, abs(self.pos))
                self.buy(bar.close + 5, self.fixedSize)

        # 发出状态更新事件
        self.putEvent()

    # ----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        pass

    # ----------------------------------------------------------------------
    def onTrade(self, trade):
        # 发出状态更新事件
        self.putEvent()


if __name__ == '__main__':
    # 提供直接双击回测的功能
    # 导入PyQt4的包是为了保证matplotlib使用PyQt4而不是PySide，防止初始化出错
    from ctaBacktesting import *
    from PyQt4 import QtCore, QtGui

    # 创建回测引擎
    engine = BacktestingEngine()

    # 设置引擎的回测模式为K线
    engine.setBacktestingMode(engine.BAR_MODE)

    # 设置回测用的数据起始日期
    engine.setStartDate('20120101')

    # 设置产品相关参数
    engine.setSlippage(0.2)  # 股指1跳
    engine.setRate(0.3 / 10000)  # 万0.3
    engine.setSize(300)  # 股指合约大小
    engine.setPriceTick(0.2)  # 股指最小价格变动

    # 设置使用的历史数据库
    engine.setDatabase(MINUTE_DB_NAME, 'IF0000')

    # 在引擎中创建策略对象
    d = {'atrLength': 11}
    engine.initStrategy(AtrRsiStrategy, d)

    # 开始跑回测
    engine.runBacktesting()

    # 显示回测结果
    engine.showBacktestingResult()

    ## 跑优化
    # setting = OptimizationSetting()                 # 新建一个优化任务设置对象
    # setting.setOptimizeTarget('capital')            # 设置优化排序的目标是策略净盈利
    # setting.addParameter('atrLength', 12, 20, 2)    # 增加第一个优化参数atrLength，起始11，结束12，步进1
    # setting.addParameter('atrMa', 20, 30, 5)        # 增加第二个优化参数atrMa，起始20，结束30，步进1
    # setting.addParameter('rsiLength', 5)            # 增加一个固定数值的参数

    ## 性能测试环境：I7-3770，主频3.4G, 8核心，内存16G，Windows 7 专业版
    ## 测试时还跑着一堆其他的程序，性能仅供参考
    # import time
    # start = time.time()

    ## 运行单进程优化函数，自动输出结果，耗时：359秒
    # engine.runOptimization(AtrRsiStrategy, setting)

    ## 多进程优化，耗时：89秒
    ##engine.runParallelOptimization(AtrRsiStrategy, setting)

    # print u'耗时：%s' %(time.time()-start)