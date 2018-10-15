# encoding: UTF-8

"""
展示如何执行策略回测。

最新修改日志：
作者: 陈卓杰
时间: 2018/10/15 12:00
内容：
(1) 使用的策略为双均线策略, 数据为数字货币XBT合约;
(2) 添加了合约保证金比例的设置, 初始资金的设置的设置;

"""

from __future__ import division
import time
from vnpy.trader.app.ctaStrategy.ctaBacktesting import BacktestingEngine, MINUTE_DB_NAME


if __name__ == '__main__':
    from vnpy.trader.app.ctaStrategy.strategy.strategy_DoubleMA import DoubleMA1Strategy

    # 创建回测引擎
    engine = BacktestingEngine()

    # 设置引擎的回测模式为K线
    engine.setBacktestingMode(engine.BAR_MODE)

    # 设置回测时间的范围
    engine.setStartDate('20180201',initDays=10)  # 第一个参数为策略开始日期, 第二个参数为往前加载多少天的数据来准备变量
    engine.setEndDate('20180901')                # 策略结束日期

    # 设置产品相关参数
    engine.setSlippage(0.5)     # 设置滑点, 设为1个跳
    engine.setRate(2/10000)     # 手续费, 先设为万2
    engine.setSize(1)           # 合约价值, 先设定为1
    engine.setMarginRate(0.01)  # 设置合约保证金比例, 这里为100倍
    engine.setPriceTick(0.5)    # bitmex.XBTUSE最小价格变动

    # 设置测试的初始资金
    engine.setInitCapital(100000)  # 设置为10w

    # 设置使用的历史数据库
    engine.setDatabase("Digital_30Min_Db", "bitmex.XBTUSD")

    # 在引擎中创建策略对象
    d = {"ma1": 20, "ma2": 60, "fixedSize":3}
    engine.initStrategy(DoubleMA1Strategy, d)

    t1 = time.time()
    # 开始跑回测
    engine.runBacktestingSimple()

    # 显示回测结果
    engine.showBacktestingResult2()

    # 画图
    engine.plotResult(saving=True)

    print(u"回测部分耗时:{:.2f}s".format(time.time()-t1))