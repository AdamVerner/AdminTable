import { IconArrowDown, IconArrowsUpDown, IconArrowUp } from '@tabler/icons-react';
import { Group, Table, Tooltip } from '@mantine/core';
import { useTableParams } from '@/pages/ResourceList/utils';

interface TableHeadProps {
  header: {
    ref: string;
    display: string;
    sortable: boolean;
    sort: 'asc' | 'desc' | null;
    description: string;
  }[];
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

export default ({ header }: TableHeadProps) => {
  const { setSort } = useTableParams();
  return (
    <>
      <Table.Thead>
        <Table.Tr>
          {header.map((col, i) => (
            <Table.Th key={i}>
              <Group>
                {col.description ? (
                  <Tooltip label={col.description}>
                    <span>{col.display}</span>
                  </Tooltip>
                ) : (
                  <span>{col.display}</span>
                )}

                {col.sortable && (
                  <DirectionArrow c_ref={col.ref} current_sort={col.sort} setSort={setSort} />
                )}
              </Group>
            </Table.Th>
          ))}
        </Table.Tr>
      </Table.Thead>
    </>
  );
};
