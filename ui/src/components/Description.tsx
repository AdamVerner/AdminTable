import { Space } from '@mantine/core';
import { MarkdownPage } from '@/components/MarkdownPage';

export const Description = ({ description }: { description: string | null }) => {
  return (
    <Space mb="xl" p="xs">
      {description ? <MarkdownPage content={description} /> : null}
    </Space>
  );
};

export default Description;
