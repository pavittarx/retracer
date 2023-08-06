import { useState, useEffect, useRef } from "react";
import { ChartOptions, DeepPartial, createChart } from "lightweight-charts";
import axios from "axios";

const Tooltip = ({ x, y, ...data }: any) => {
  return (
    <>
      <div
        style={{
          position: "absolute",
          left: x - 100,
          top: y - 200,
          height: 150,
          width: 200,
          zIndex: 10,

          border: "1px solid #ff000010",
          background: "#ffffffa0",
        }}
      >
        <div>Close : {data?.close?.toFixed(5)}</div>
        <div>SMA : {data?.sma?.toFixed(5)}</div>
        <div>LMA : {data?.lma?.toFixed(5)}</div>
        <div>
          Diff : {(data?.lma?.toFixed(5) - data?.sma?.toFixed(5))?.toFixed(5)}
        </div>
      </div>
    </>
  );
};

export default function Home() {
  const ref = useRef<HTMLDivElement>(null);
  const [tooltip, setTooltip] = useState<any>(null);

  useEffect(() => {
    if (!ref.current) return;

    const chartOptions = {
      layout: {
        textColor: "black",
        background: { type: "solid", color: "white" },
      },
    };
    const chart = createChart(
      ref.current as HTMLElement,
      chartOptions as DeepPartial<ChartOptions>
    );

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: "#26a69a",
      downColor: "#ef5350",
      borderVisible: false,
      wickUpColor: "#26a69a",
      wickDownColor: "#ef5350",
    });

    const lineSeries = chart.addLineSeries({ color: "#2962FF" });
    const lineSeries2 = chart.addLineSeries({ color: "#808000" });

    axios.get("/data.json").then((res: any) => {
      const candles = res.data.candles.map((c: any) => ({
        ...c,
        dx: c.dx / 1000,
      }));

      console.log(candles);

      candlestickSeries.setData(
        candles.map((c: any) => ({
          time: c.dx,
          open: c.Open,
          high: c.High,
          low: c.Low,
          close: c.Close,
          sma: c.small_ema,
          lma: c.large_ema,
        }))
      );

      lineSeries.setData(
        candles.map((c: any) => ({
          time: c.dx,
          value: c.small_ema,
        }))
      );

      lineSeries2.setData(
        candles.map((c: any) => ({
          time: c.dx,
          value: c.large_ema,
        }))
      );

      candlestickSeries.setMarkers(
        candles
          .filter((c: any) => c.signal)
          .map((c: any) => ({
            time: c.dx,
            position: "aboveBar",
            color: "#f68410",
            shape: "circle",
            text: "signal",
          }))
      );

      chart.subscribeCrosshairMove((param: any) => {
        if (!param?.time) return;

        const data = param.seriesData.get(candlestickSeries);
        const sma = param.seriesData.get(lineSeries);
        const lma = param.seriesData.get(lineSeries2);

        console.log(param);

        setTooltip({
          ...param?.point,
          ...(data || {}),
          sma: sma.value,
          lma: lma.value,
        });
      });
    });

    chart.timeScale().applyOptions({
      borderColor: "#71649C",
      // barSpacing: 10,
      timeVisible: true,
    });
  }, [ref]);

  return (
    <main>
      <Tooltip {...tooltip} />
      <div
        ref={ref}
        id="chart"
        style={{ position: "relative", height: "90vh", width: "99vw" }}
      ></div>
    </main>
  );
}
