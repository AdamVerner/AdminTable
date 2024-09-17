import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  Button,
  Center,
  Checkbox,
  Grid,
  Input,
  Loader,
  NumberInput,
  Title,
  Tooltip,
} from '@mantine/core';
import { useForm, UseFormReturnType } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import dataService from '@/services/data.service';

interface ActionProps {
  action: {
    title: string;
    ref: string;
    description: string;
    parameters: {
      attr: string;
      title: string;
      type: string;
      required: boolean;
      description: string | null;
    }[];
  };
}

interface ActionParamInputProps {
  p: ActionProps['action']['parameters'][0];
  form: UseFormReturnType<any>;
}

const ActionParamInput = ({ p, form }: ActionParamInputProps) => {
  const widget = (() => {
    switch (p.type) {
      case 'int':
        return (
          <NumberInput
            placeholder={p.title}
            required={p.required}
            {...form.getInputProps(p.attr)}
          />
        );
      case 'bool':
        return (
          <Checkbox
            required={p.required}
            placeholder={p.title}
            label={p.title}
            {...form.getInputProps(p.attr)}
          />
        );
      default:
        return (
          <Input required={p.required} placeholder={p.title} {...form.getInputProps(p.attr)} />
        );
    }
  })();

  if (p.description === null) {
    return widget;
  }

  return <Tooltip label={<p>{p.description}</p>}>{widget}</Tooltip>;
};
export const Action = ({ action }: ActionProps) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { resourceName, detailId } = useParams();
  const form = useForm({
    mode: 'uncontrolled',
    initialValues: Object.fromEntries(
      action.parameters.map((p) => {
        return [p.attr, null];
      })
    ),
  });

  if (isSubmitting) {
    return (
      <Center>
        <Loader />
      </Center>
    );
  }

  const onSubmit = () => {
    setIsSubmitting(true);
    const params = form.getValues();
    dataService.executeAction(resourceName!, detailId!, action.ref, params).then(
      (res) => {
        notifications.show({
          title: res.failed ? 'Action Failed' : 'Action Success',
          message: res.message,
          color: res.failed ? 'red' : 'blue',
          autoClose: res.failed ? 15000 : 5000,
        });
        setIsSubmitting(false);
      },
      (err) => {
        notifications.show({
          title: `Action Failed`,
          message: `Failed: ${err}`,
          color: 'red',
          autoClose: 15000,
        });
        setIsSubmitting(false);
      }
    );
  };

  return (
    <Grid>
      <Grid.Col span={{ base: 3 }}>
        <Title order={3}>{action.title}</Title>
      </Grid.Col>
      {action.parameters.map((p, i) => (
        <Grid.Col key={i} span="auto">
          <ActionParamInput p={p} form={form} />
        </Grid.Col>
      ))}
      <Grid.Col span={{ base: 3 }}>
        <Button ml="auto" onClick={onSubmit}>
          Submit
        </Button>
      </Grid.Col>
    </Grid>
  );
};
