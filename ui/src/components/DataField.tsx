import React, { useState } from 'react';
import { IconEye } from '@tabler/icons-react';
import { Link } from 'react-router-dom';
import { Anchor, Code, Group, Modal, Text, Title, TypographyStylesProvider } from '@mantine/core';
import { MarkdownPage } from '@/components/MarkdownPage';
import { linkBuilder } from '@/RouterControl';

export const fix_title = (title: string): string => {
  if (title.startsWith('[[html]]')) {
    return title.slice(8);
  }
  if (title.startsWith('[[markdown]]')) {
    return title.slice(12);
  }
  if (title.startsWith('[[json]]')) {
    return title.slice(8);
  }
  return title;
};

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
  const is_html = title?.startsWith('[[html]]');
  const is_markdown = title?.startsWith('[[markdown]]');
  const is_json = title?.startsWith('[[json]]');
  const in_modal = is_long || is_html || is_markdown || is_json;

  if (!in_modal) {
    return <Text>{value}</Text>;
  }
  let modal_content;
  if (is_html) {
    modal_content = (
      <TypographyStylesProvider>
        <div dangerouslySetInnerHTML={{ __html: value }} />
      </TypographyStylesProvider>
    );
  } else if (is_markdown) {
    modal_content = <MarkdownPage content={value} />;
  } else if (is_json) {
    modal_content = <Code block>{JSON.stringify(JSON.parse(value), undefined, 2)}</Code>;
  } else {
    modal_content = <Text>{value}</Text>;
  }

  const short_content = value.slice(0, BREAK);

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
        title={<Title order={1}>{fix_title(title || '')}</Title>}
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
    if (!cell.resource || !cell.id) {
      return <Extendable title={title} value="" />;
    }
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
