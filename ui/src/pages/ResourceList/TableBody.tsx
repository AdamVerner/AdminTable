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
}

const TableRow = ({ row }: { row: TableBodyProps['rows'][0] }) => {
  return (
    <Table.Tr>
      {row.map((cell, i) => (
        <Table.Td key={i}>
          <DataField cell={cell} />
        </Table.Td>
      ))}
    </Table.Tr>
  );
};

export default ({ rows }: TableBodyProps) => {
  return (
    <Table.Tbody>
      {rows.map((row, i) => (
        <TableRow row={row} key={i} />
      ))}
    </Table.Tbody>
  );
};
