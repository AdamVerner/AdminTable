import { Table } from '@mantine/core';
import DataField from '@/components/DataField';

interface TableBodyProps {
  rows: (
    | string
    | {
        type: 'link';
        kind: 'detail';
        resource: string;
        value: string;
        id: string;
      }
    | {
        type: 'link';
        kind: 'table';
        resource: string;
        value: string;
        filter: {
          col: string;
          op: string;
          val: string;
        };
      }
  )[][];
  header: {
    ref: string;
    display: string;
    sortable: boolean;
    sort: 'asc' | 'desc' | null;
    description: string;
  }[];
}

const TableRow = ({
  header,
  row,
}: {
  header: TableBodyProps['header'];
  row: TableBodyProps['rows'][0];
}) => {
  return (
    <Table.Tr>
      {row.map((cell, i) => (
        <Table.Td key={i}>
          <DataField title={header[i].display} cell={cell} />
        </Table.Td>
      ))}
    </Table.Tr>
  );
};

export default ({ header, rows }: TableBodyProps) => {
  return (
    <Table.Tbody>
      {rows.map((row, i) => (
        <TableRow header={header} row={row} key={i} />
      ))}
    </Table.Tbody>
  );
};
