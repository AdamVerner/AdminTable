import { IconArrowDown, IconArrowsUpDown, IconArrowUp } from '@tabler/icons-react';
import { Table } from '@mantine/core';
import FieldTitle from '@/components/FieldTitle';

interface TableHeadProps {
  header: {
    ref: string;
    display: string;
    sortable: boolean;
    sort: 'asc' | 'desc' | null;
    description: string;
  }[];
  setSort: (sort: { ref: string; dir: 'asc' | 'desc' }) => void;
}

const DirectionArrow = (props: {
  c_ref: string;
  current_sort: 'asc' | 'desc' | null;
  setSort: (sort: { ref: string; dir: 'asc' | 'desc' }) => void;
}) => {
  const defaultProps = {
    role: 'button',
    style: { cursor: 'pointer' },
    size: '1rem',
  };
  switch (props.current_sort) {
    case 'asc':
      return (
        <IconArrowUp
          {...defaultProps}
          onClick={() => props.setSort({ ref: props.c_ref, dir: 'desc' })}
        />
      );
    case 'desc':
      return (
        <IconArrowDown
          {...defaultProps}
          onClick={() => props.setSort({ ref: props.c_ref, dir: 'asc' })}
        />
      );
    default:
      return (
        <IconArrowsUpDown
          {...defaultProps}
          onClick={() => props.setSort({ ref: props.c_ref, dir: 'asc' })}
        />
      );
  }
};

export default ({ header, setSort }: TableHeadProps) => {
  return (
    <>
      <Table.Thead>
        <Table.Tr>
          {header.map((col, i) => (
            <Table.Th key={i}>
              <FieldTitle display={col.display} description={col.description}>
                {col.sortable && (
                  <DirectionArrow c_ref={col.ref} current_sort={col.sort} setSort={setSort} />
                )}
              </FieldTitle>
            </Table.Th>
          ))}
        </Table.Tr>
      </Table.Thead>
    </>
  );
};
