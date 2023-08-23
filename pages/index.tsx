import { useState, useEffect, useRef } from "react";
import { ChartOptions, DeepPartial, createChart } from "lightweight-charts";
import axios from "axios";

const Tooltip = ({ x, y, ...data }: any) => {
  console.log("dx", data);

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
        <div>SMA High : {data?.sma_high?.toFixed(5)}</div>
        <div>SMA Low : {data?.sma_low?.toFixed(5)}</div>
        <div>LMA : {data?.lma?.toFixed(5)}</div>
        <div>
          Low Diff : {data?.lma?.toFixed(5) - data?.sma_low?.toFixed(5)}
        </div>
        <div>
          High Diff : {data?.lma?.toFixed(5) - data?.sma_high?.toFixed(5)}
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

    const lineSeriesSMA_low = chart.addLineSeries({ color: "#2962FF" });
    const lineSeriesSMA_high = chart.addLineSeries({ color: "#e2821c" });
    const lineSeries2 = chart.addLineSeries({ color: "#808000" });

    axios.get("/data.json").then((res: any) => {
      const candles = res.data.candles
        .sort((a: any, b: any) => a.time - b.time)
        .map((c: any) => ({
          ...c,
          dx: c.dx / 1000,
        }));

      console.log(candles);

      candlestickSeries.setData(
        candles.map((c: any) => ({
          time: c.time,
          open: c.open,
          high: c.high,
          low: c.low,
          close: c.close,
        }))
      );

      lineSeriesSMA_low.setData(
        candles.map((c: any) => ({
          time: c.time,
          value: c.small_ema_low,
        }))
      );

      lineSeriesSMA_high.setData(
        candles.map((c: any) => ({
          time: c.time,
          value: c.small_ema_high,
        }))
      );

      lineSeries2.setData(
        candles.map((c: any) => ({
          time: c.time,
          value: c.large_ema,
        }))
      );

      candlestickSeries.setMarkers(
        candles
          .filter((c: any) => c.signal)
          .map((c: any) => ({
            time: c.time,
            position: "aboveBar",
            color: "#f68410",
            shape: "circle",
            text: "signal",
          }))
      );

      chart.subscribeCrosshairMove((param: any) => {
        if (!param?.time) return;

        const data = param.seriesData.get(candlestickSeries);
        const sma_low = param.seriesData.get(lineSeriesSMA_low);
        const sma_high = param.seriesData.get(lineSeriesSMA_high);
        const lma = param.seriesData.get(lineSeries2);

        console.log(param);

        setTooltip({
          ...param?.point,
          ...(data || {}),
          sma_low: sma_low.value,
          sma_high: sma_high.value,
          lma: lma.value,
        });
      });
    });

    chart.timeScale().applyOptions({
      borderColor: "#71649C",
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
