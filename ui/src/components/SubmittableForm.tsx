import React, { useEffect, useState } from 'react';
import Form from '@aokiapp/rjsf-mantine-theme';
import { IChangeEvent } from '@rjsf/core';
import validator from '@rjsf/validator-ajv8';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Container, Stack } from '@mantine/core';
import actionResponseHandler from '@/components/actionResponseHandler';
import { MarkdownPage } from '@/components/MarkdownPage';

export interface SubmittableFormProps {
  title?: string;
  description?: string;
  schema: any;
  onSubmit: (formData: any) => Promise<{
    message: string;
    failed?: true;
    redirect?:
      | { type: 'detail'; resource: string; id: string }
      | { type: 'list'; resource: string; filters: { ref: string; op: string; val: string }[] }
      | { type: 'customPage'; name: string };
  }>;
}

export default function SubmittableForm(props: SubmittableFormProps) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [formData, setFormData] = useState<object>(Object.fromEntries(searchParams));
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    setFormData({ ...formData, ...Object.fromEntries(searchParams) });
  }, [searchParams]);

  const onSubmit = (event: IChangeEvent): void => {
    setIsSubmitting(true);
    actionResponseHandler(props.onSubmit(event.formData), navigate).finally(() => {
      setIsSubmitting(false);
    });
  };

  const uiSchema = {
    'ui:submitButtonOptions': {
      props: {
        loading: isSubmitting,
        style: { marginTop: '2em' },
      },
    },
  };
  const title = props.title ?? props.schema.title;
  const description = props.description ?? props.schema.description;
  return (
    <Container>
      <Stack>
        <h1>{title}</h1>
        {description && <MarkdownPage content={description} />}
        <Form
          schema={{ ...props.schema, title: undefined, description: undefined }}
          uiSchema={uiSchema}
          formData={formData}
          onChange={(formState) => {
            setFormData(formState.formData);
          }}
          validator={validator}
          disabled={isSubmitting}
          onSubmit={onSubmit}
        />
      </Stack>
    </Container>
  );
}
