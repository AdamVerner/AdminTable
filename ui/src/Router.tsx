import React, { useEffect, useState } from 'react';
import {
  createHashRouter,
  Navigate,
  Outlet,
  redirect,
  RouterProvider,
  useLocation,
} from 'react-router-dom';
import Loader from '@/components/Loader';
import CustomPage from '@/pages/CustomPage.page';
import HomeDashboardPage from '@/pages/HomeDashboard.page';
import InputFormPage from '@/pages/InputForm.page';
import CreateResourcePage from '@/pages/ResourceCreate';
import ResourceDetail from '@/pages/ResourceDetail';
import ResourceListPage from '@/pages/ResourceList';
import { authService } from '@/services/auth';
import { Layout } from './Layout';
import { LoginPage } from './pages/Login.page';

interface UserLoginHandlerProps {
  loggedInComponent?: React.ReactNode;
  notLoggedInComponent?: React.ReactNode;
}

const UserLoginHandler = ({ loggedInComponent, notLoggedInComponent }: UserLoginHandlerProps) => {
  const [loading, setLoading] = useState(true);
  const [loggedIn, setLoggedIn] = useState(false);

  useEffect(() => {
    authService
      .isUserLoggedIn()
      .then((loggedIn) => {
        setLoggedIn(loggedIn);
      })
      .catch(() => setLoggedIn(false))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <Loader />;
  }

  return loggedIn ? loggedInComponent : notLoggedInComponent;
};

const ProtectedRoutes = () => {
  const location = useLocation();

  return (
    <UserLoginHandler
      loggedInComponent={<Outlet />}
      notLoggedInComponent={<Navigate to="/login" replace state={{ from: location }} />}
    />
  );
};

const LayoutMaybeLoggedIn = () => {
  return <UserLoginHandler loggedInComponent={<Layout />} notLoggedInComponent={<Outlet />} />;
};

const router = createHashRouter(
  [
    {
      path: '/',
      element: <ProtectedRoutes />,
      children: [
        {
          path: '/',
          element: <Layout />,
          children: [
            {
              path: '/',
              element: <HomeDashboardPage />,
            },
            {
              path: 'resource/:resourceName/list',
              element: <ResourceListPage />,
            },
            {
              path: 'resource/:resourceName/create',
              element: <CreateResourcePage />,
            },
            {
              path: 'resource/:resourceName/detail/:detailId',
              element: <ResourceDetail />,
            },
          ],
        },
      ],
    },
    {
      path: '/page',
      element: <LayoutMaybeLoggedIn />,
      children: [
        {
          path: ':pageName',
          element: <CustomPage />,
        },
      ],
    },
    {
      path: '/forms',
      element: <LayoutMaybeLoggedIn />,
      children: [
        {
          path: ':formName',
          element: <InputFormPage />,
        },
      ],
    },
    {
      path: '/login',
      Component: LoginPage,
    },
    {
      path: '/logout',
      async loader() {
        authService.logout();
        return redirect('/login');
      },
    },
  ],
  {}
);

export default function Router() {
  return <RouterProvider router={router} />;
}
