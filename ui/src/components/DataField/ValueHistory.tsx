import { useEffect, useState } from 'react';
import { Table, Tooltip } from '@mantine/core';

export interface ValueHistoryProps {
  value: string;
  history_length?: number;
}

const generateSVGGraph = (values: number[]) => {
  const height = 25;
  const width = 250;

  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const avgValue = values.reduce((acc, value) => acc + value, 0) / values.length;
  const length = values.length;

  // X position
  const get_x = (index: number) => (index / length) * width + 1;
  // Y position (inverted)
  const get_y = (value: number) =>
    height - 2 - ((value - minValue) / (maxValue - minValue)) * (height - 2) + 1;

  // Create the path data for the line chart
  let pathData = '';
  values.forEach((value, index) => {
    pathData += `${index === 0 ? 'M' : 'L'}${get_x(index)},${get_y(value)} `;
  });

  const min_x = get_x(values.indexOf(minValue));
  const max_x = get_x(values.indexOf(maxValue));

  return (
    <svg
      style={{ position: 'absolute', top: 1, left: 1, height: '100%', width: '100%' }}
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path d={pathData} stroke="blue" fill="none" stroke-width="1" />
      <path d={`M${min_x},0 ` + `L${min_x},${get_y(minValue)} `} stroke="magenta" strokeWidth={1} />
      <path
        d={`M${max_x},${height} ` + `L${max_x},${get_y(maxValue)} `}
        stroke="magenta"
        strokeWidth={1}
      />
      <path
        d={`M0,${get_y(avgValue)} ` + `L${width},${get_y(avgValue)} `}
        stroke="gray"
        strokeWidth={2}
        vectorEffect="non-scaling-stroke"
        strokeDasharray="4 4"
      />
    </svg>
  );
};

export default (props: ValueHistoryProps) => {
  const [valueHistory, setValueHistory] = useState<[string, Date][]>([[props.value, new Date()]]);
  const values = valueHistory.map(([value, date]) => [parseInt(value, 10), date] as [number, Date]);

  useEffect(() => {
    setValueHistory(
      [...valueHistory, [props.value, new Date()] as [string, Date]].slice(
        -(props?.history_length ?? 50)
      )
    );
  }, [props.value]);

  const svg = generateSVGGraph(values.map(([v]) => v));
  const min: [number, Date] = values.reduce(
    (acc, [value, date]) => (acc[0] < value ? acc : [value, date]),
    [Infinity, new Date()]
  );
  const max: [number, Date] = values.reduce(
    (acc, [value, date]) => (acc[0] > value ? acc : [value, date]),
    [-Infinity, new Date()]
  );
  const avg: number = values.reduce((acc, [value]) => acc + value, 0) / values.length;
  return (
    <div style={{ flexGrow: 1, position: 'relative', alignSelf: 'stretch', marginRight: '1em' }}>
      <Tooltip
        label={
          <Table>
            <Table.Tbody>
              <Table.Tr>
                <Table.Td>First</Table.Td>
                <Table.Td>{valueHistory[0][0]}</Table.Td>
                <Table.Td>{valueHistory[0][1].toLocaleTimeString()}</Table.Td>
              </Table.Tr>
              <Table.Tr>
                <Table.Td>Last</Table.Td>
                <Table.Td>{valueHistory[valueHistory.length - 1][0]}</Table.Td>
                <Table.Td>{valueHistory[valueHistory.length - 1][1].toLocaleTimeString()}</Table.Td>
              </Table.Tr>
              <Table.Tr>
                <Table.Td>Min</Table.Td>
                <Table.Td>{min[0]}</Table.Td>
                <Table.Td>{min[1].toLocaleTimeString()}</Table.Td>
              </Table.Tr>
              <Table.Tr>
                <Table.Td>Max</Table.Td>
                <Table.Td>{max[0]}</Table.Td>
                <Table.Td>{max[1].toLocaleTimeString()}</Table.Td>
              </Table.Tr>
              <Table.Tr>
                <Table.Td>Avg</Table.Td>
                <Table.Td>{avg.toFixed(2)}</Table.Td>
                <Table.Td>-</Table.Td>
              </Table.Tr>
            </Table.Tbody>
          </Table>
        }
        position="left"
        withArrow
      >
        {svg}
      </Tooltip>
    </div>
  );
};
