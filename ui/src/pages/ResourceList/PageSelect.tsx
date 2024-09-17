import { Affix, Group, Pagination, Select } from '@mantine/core';

interface PageSelectProps {
  total: number;
  page: number;
  perPage: number;
  setPage: (page: number) => void;
  setPerPage: (perPage: number) => void;
  float?: boolean;
}
export default ({ total, page, perPage, setPage, setPerPage, float = true }: PageSelectProps) => {
  const totalPages = total / (perPage ?? 50);
  const control = (
    <Group>
      <Pagination
        value={page}
        total={totalPages}
        withControls={false}
        withEdges
        onChange={(value) => {
          setPage(value);
        }}
      />

      <Select
        value={`${perPage}`}
        data={['1', '10', '20', '50', '100', '200']}
        allowDeselect={false}
        onChange={(value) => {
          setPerPage(parseInt(value!, 10));
        }}
      />
    </Group>
  );
  if (!float) {
    return control;
  }
  return (
    <Affix position={{ bottom: 40, left: '50%' }} style={{ transform: 'translateX(-50%)' }}>
      {control}
    </Affix>
  );
};
