import { Box, Group, Pagination, Paper, Select } from '@mantine/core';

interface PageSelectProps {
  total: number;
  page: number;
  perPage: number;
  setPage: (page: number) => void;
  setPerPage: (perPage: number) => void;
  float?: boolean;
}
export default ({ total, page, perPage, setPage, setPerPage, float = true }: PageSelectProps) => {
  const totalPages = Math.ceil(total / (perPage ?? 50));
  const control = (
    <Group wrap="nowrap" justify="space-between">
      <div>
        {page * perPage - perPage + 1}-{Math.min(page * perPage, total)}/{total}
      </div>
      <Group>
        <Pagination
          value={page}
          total={totalPages}
          withControls={false}
          siblings={1}
          onChange={(value) => {
            setPage(value);
          }}
          style={{ flexWrap: 'nowrap' }}
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
    </Group>
  );
  if (!float) {
    return <Box my="xs">{control}</Box>;
  }
  return (
    <Box pos="sticky" bottom={40}>
      <Paper px="md" py="xs" radius="md" bg="var(--mantine-color-default-hover)">
        {control}
      </Paper>
    </Box>
  );
};
