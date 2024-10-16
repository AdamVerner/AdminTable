import { IconX } from '@tabler/icons-react';
import { Badge, Button, Group, Input, Select, Stack } from '@mantine/core';
import { useForm } from '@mantine/form';
import { useTableParams } from '@/pages/ResourceList/utils';

export const operators = {
  eq: '=',
  ne: '!=',
  lt: '<',
  le: '<=',
  gt: '>',
  ge: '>=',
  in: 'in',
  like: 'like',
  ilike: 'ilike',
  is_null: 'is null',
  is_not_null: 'is not null',
};

interface AddFilterProps {
  applied_filters: FilterSelectionProps['applied_filters'];
  available_filters: FilterSelectionProps['available_filters'];
  setFilters: (filters: { ref: string; op: string; val: string }[]) => void;
}

function AddFilter({ available_filters, applied_filters, setFilters }: AddFilterProps) {
  const form = useForm({
    initialValues: {
      ref: available_filters[0].ref,
      op: 'eq',
      val: '',
    },
  });
  const onAddFilter = () => {
    const { ref, op, val } = form.getValues();
    setFilters([...applied_filters, { ref, op, val }]);
  };
  return (
    <Group>
      <Select
        searchable
        {...form.getInputProps('ref')}
        data={available_filters.map((af) => ({ value: af.ref, label: af.display }))}
      />
      <Select
        {...form.getInputProps('op')}
        style={{ width: '8ch' }}
        data={Object.entries(operators).map(([k, v]) => ({ value: k, label: v }))}
      />
      {form.getValues().op === 'is_null' || form.getValues().op === 'is_not_null' ? null : (
        <Input placeholder="value" {...form.getInputProps('val')} />
      )}
      <Button onClick={onAddFilter}>Add Filter</Button>
    </Group>
  );
}

interface AppliedFilterProps {
  f: {
    ref: string;
    op: string;
    val: string;
    display?: string;
  };
  applied_filters: FilterSelectionProps['applied_filters'];
  setFilters: (filters: { ref: string; op: string; val: string }[]) => void;
}
function AppliedFilter({ f, applied_filters, setFilters }: AppliedFilterProps) {
  const Remove = () => {
    return (
      <IconX
        size="1rem"
        style={{ cursor: 'pointer' }}
        onClick={() => {
          setFilters(
            applied_filters.filter((f2) => f2.ref !== f.ref || f2.op !== f.op || f2.val !== f.val)
          );
        }}
      >
        X
      </IconX>
    );
  };

  return (
    <Badge tt="none" rightSection={<Remove />}>
      {f.display}
      &nbsp;
      {operators?.[f.op as keyof typeof operators] ?? f.op}
      &nbsp;
      <b>{f.val}</b>
    </Badge>
  );
}
interface FilterSelectionProps {
  applied_filters: {
    ref: string;
    op: string;
    val: string;
    display?: string;
  }[];
  available_filters: {
    ref: string;
    display: string;
  }[];
}

export default ({ applied_filters, available_filters }: FilterSelectionProps) => {
  const {
    state: { filters },
    setFilters,
  } = useTableParams();
  return (
    <Stack>
      <AddFilter
        available_filters={available_filters}
        applied_filters={applied_filters}
        setFilters={setFilters}
      />
      <Group>
        {applied_filters.map((filter, i) => (
          <AppliedFilter key={i} applied_filters={filters} f={filter} setFilters={setFilters} />
        ))}
      </Group>
    </Stack>
  );
};
