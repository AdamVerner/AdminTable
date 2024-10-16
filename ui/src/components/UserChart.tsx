import React from 'react';
import { AreaChart, BarChart, LineChart } from '@mantine/charts';
import { Text } from '@mantine/core';

interface UserChartProps {
  type: 'line' | 'bar' | 'area';
  config: {
    data: Record<string, any>[];
    dataKey: string;
    series: { name: string; color: string; [key: string]: any }[];
    [key: string]: any;
  };
}

export const UserChart = ({ type, config }: UserChartProps) => {
  const graphLut = {
    line: LineChart,
    bar: BarChart,
    area: AreaChart,
  };
  const ChartComponent = graphLut[type];
  if (!ChartComponent) {
    return <Text c="red">Invalid chart type: "{type}"</Text>;
  }

  try {
    return <ChartComponent h={300} {...config} />;
  } catch (e: any) {
    return <Text c="red">Error rendering chart: {e?.message}</Text>;
  }
};
export default UserChart;
