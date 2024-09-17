import { IconArrowDown, IconArrowsUpDown, IconArrowUp } from '@tabler/icons-react';
import { Group, Table, Tooltip } from '@mantine/core';
import { useTableParams } from '@/pages/ResourceList/utils';

interface TableHeadProps {
  header: { ref: string; display: string; sortable: boolean; description: string }[];
}

const DirectionArrow = (props: {
  c_ref: string;
  current_sort: { ref: string; dir: string } | undefined;
  setSort: (sort: { ref: string; dir: 'asc' | 'desc' }) => void;
}) => {
  const defaultProps = {
    role: 'button',
    style: { cursor: 'pointer' },
    size: '1rem',
  };
  if (props.current_sort?.ref === props.c_ref) {
    if (props.current_sort?.dir === 'asc') {
      return (
        <IconArrowUp
          {...defaultProps}
          onClick={() => props.setSort({ ref: props.c_ref, dir: 'desc' })}
        />
      );
    } else if (props.current_sort?.dir === 'desc') {
      return (
        <IconArrowDown
          {...defaultProps}
          onClick={() => props.setSort({ ref: props.c_ref, dir: 'asc' })}
        />
      );
    }
  }
  return (
    <IconArrowsUpDown
      {...defaultProps}
      onClick={() => props.setSort({ ref: props.c_ref, dir: 'asc' })}
    />
  );
};

export default ({ header }: TableHeadProps) => {
  const { state: SearchState, setSort } = useTableParams();
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
                  <DirectionArrow
                    c_ref={col.ref}
                    current_sort={SearchState.sort}
                    setSort={setSort}
                  />
                )}
              </Group>
            </Table.Th>
          ))}
        </Table.Tr>
      </Table.Thead>
    </>
  );
};
