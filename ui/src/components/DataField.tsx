import React, { useState } from 'react';
import { IconEye } from '@tabler/icons-react';
import { Link } from 'react-router-dom';
import { Anchor, Group, Modal, Text, Title, TypographyStylesProvider } from '@mantine/core';
import { MarkdownPage } from '@/components/MarkdownPage';
import { linkBuilder } from '@/RouterControl';

const Extendable = ({ title, value }: { title?: string; value: string | any }) => {
  const [opened, setOpened] = useState(false);
  const handleOpen = () => setOpened(true);
  const handleClose = () => setOpened(false);

  if (typeof value !== 'string') {
    return <Text>{JSON.stringify(value)}</Text>;
  }
  const BREAK = 25;
  // exception for UUIDs
  const is_long = value.length > BREAK && !value.match(/\w{8}(-\w{4}){3}-\w{12}/g);
  const is_html = value.startsWith('[[html]]');
  const is_markdown = value.startsWith('[[markdown]]');
  const in_modal = is_long || is_html || is_markdown;

  if (!in_modal) {
    return <Text>{value}</Text>;
  }
  const content = is_html ? value.slice(8) : is_markdown ? value.slice(12) : value;
  let modal_content;
  if (is_html) {
    modal_content = (
      <TypographyStylesProvider>
        <div dangerouslySetInnerHTML={{ __html: content }} />
      </TypographyStylesProvider>
    );
  } else if (is_markdown) {
    modal_content = <MarkdownPage content={content} />;
  } else {
    modal_content = <Text>{content}</Text>;
  }

  const short_content = (
    is_html
      ? content.replace(/<.*?>/g, ' ')
      : is_markdown
        ? content.replace(/[^\w\s]/g, ' ')
        : content
  ).slice(0, BREAK);

  return (
    <div>
      <Group justify="space-between">
        <Text inline>{short_content} ...</Text>
        <Anchor pr="md" underline="always" onClick={handleOpen}>
          <IconEye size={16} />
        </Anchor>
      </Group>

      <Modal
        opened={opened}
        onClose={handleClose}
        size="auto"
        title={<Title order={1}>{title}</Title>}
      >
        {modal_content}
      </Modal>
    </div>
  );
};

export interface DataFieldProps {
  title?: string;
  cell:
    | string
    | number
    | boolean
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
      };
}

export default ({ cell, title }: DataFieldProps) => {
  if (typeof cell !== 'object' || !cell) {
    return <Extendable title={title} value={`${cell}`} />;
  }
  if (cell.type === 'link' && cell.kind === 'detail') {
    return (
      <Link to={linkBuilder.ResourceDetail(cell.resource, cell.id)}>
        <Extendable title={title} value={cell.value} />
      </Link>
    );
  }
  if (cell.type === 'link' && cell.kind === 'table') {
    return (
      <Link
        to={linkBuilder.ResourceList(cell.resource, [
          { ref: cell.filter.col, op: cell.filter.op, val: cell.filter.val },
        ])}
      >
        <Extendable title={title} value={cell.value} />
      </Link>
    );
  }
  return JSON.stringify(cell);
};
