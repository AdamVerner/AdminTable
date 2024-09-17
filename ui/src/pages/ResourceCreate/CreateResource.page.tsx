import React, { useState } from 'react';
import Form from '@aokiapp/rjsf-mantine-theme';
import { IChangeEvent } from '@rjsf/core';
import validator from '@rjsf/validator-ajv8';
import { useNavigate, useParams } from 'react-router-dom';
import { Center, Container, Loader, Stack } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { useTableParams } from '@/pages/ResourceList/utils';
import { linkBuilder } from '@/RouterControl';
import dataService, { useGetData } from '@/services/data.service';

export default () => {
  const { state: SearchState } = useTableParams();
  const { resourceName } = useParams();
  const navigate = useNavigate();
  const [formData, setFormData] = useState<object>();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [data, isLoading, failed] = useGetData(async () => {
    return await dataService.getCreate(resourceName!);
  }, [resourceName, JSON.stringify(SearchState)]);

  if (isLoading || !data || failed) {
    return (
      <Center style={{ height: '100vh' }}>
        <Loader size="xl" />
      </Center>
    );
  }
  const uiSchema = {
    'ui:submitButtonOptions': {
      props: {
        loading: isSubmitting,
        style: { marginTop: '2em' },
      },
    },
  };

  const onSubmit = ({ formData }: IChangeEvent): void => {
    setIsSubmitting(true);
    dataService
      .createResource(resourceName!, formData)
      .then((resp) => {
        notifications.show({
          title: resp.failed ? 'Failed' : 'Success',
          message: resp.message,
          color: resp.failed ? 'red' : 'blue',
        });
        setIsSubmitting(false);
        if (resp?.redirect) {
          if (resp.redirect.type === 'detail') {
            navigate(linkBuilder.ResourceDetail(resourceName!, resp.redirect.id));
          } else if (resp.redirect.type === 'table') {
            navigate(linkBuilder.ResourceList(resourceName!, resp.redirect.filters));
          }
        }
      })
      .catch((reason: any) => {
        notifications.show({
          title: 'Failed',
          message: `Failed: ${reason}`,
          color: 'red',
          autoClose: 15000,
        });
        setIsSubmitting(false);
      });
  };

  return (
    <Container>
      <Stack>
        <h1>{data.schema.title}</h1>
        {data.schema.description && <p>{data.schema.description}</p>}
        <Form
          schema={{ ...data.schema, title: undefined, description: undefined }}
          uiSchema={uiSchema}
          formData={formData}
          onChange={(formState) => {
            setFormData(formState.formData);
          }}
          validator={validator}
          onSubmit={onSubmit}
        />
      </Stack>
    </Container>
  );
};
