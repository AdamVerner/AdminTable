import React, { useState } from 'react';
import { IconEye } from '@tabler/icons-react';
import { Anchor, Code, Group, Modal, Text, Title, TypographyStylesProvider } from '@mantine/core';
import { MarkdownPage } from '@/components/MarkdownPage';

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

export interface ExtendableProps {
  title?: string;
  value: string | any;
}

export default ({ title, value: value_ }: ExtendableProps) => {
  const [opened, setOpened] = useState(false);
  const handleOpen = () => setOpened(true);
  const handleClose = () => setOpened(false);

  let value: string;
  if (typeof value_ !== 'string') {
    value = JSON.stringify(value_);
  } else {
    value = value_;
  }

  console.log('value', title, typeof value, value);

  const BREAK = 25;
  // exception for UUIDs
  const is_long = value.length > BREAK && !value.match(/\w{8}(-\w{4}){3}-\w{12}/g);
  const is_html = title?.toLowerCase()?.startsWith('[[html]]');
  const is_markdown = title?.toLowerCase()?.startsWith('[[markdown]]');
  const is_json = title?.toLowerCase()?.startsWith('[[json]]');
  const in_modal = is_long || is_html || is_markdown || is_json;

  if (!in_modal || value.length < BREAK) {
    return <Text style={{ minWidth: '3em' }}>{value}</Text>;
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
    try {
      modal_content = <Code block>{JSON.stringify(JSON.parse(value), undefined, 2)}</Code>;
    } catch (e) {
      modal_content = <Code block>value</Code>;
    }
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
        title={
          <Title order={1} component="span">
            {fix_title(title || '')}
          </Title>
        }
      >
        {modal_content}
      </Modal>
    </div>
  );
};
