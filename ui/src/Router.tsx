import React from 'react';
import {
  createHashRouter,
  Navigate,
  Outlet,
  redirect,
  RouterProvider,
  useLocation,
} from 'react-router-dom';
import CustomPage from '@/pages/CustomPage.page';
import CreateResourcePage from '@/pages/ResourceCreate';
import ResourceDetail from '@/pages/ResourceDetail';
import ResourceListPage from '@/pages/ResourceList';
import { authService } from '@/services/auth';
import { Layout } from './Layout';
import HomePage from './pages/Home.page';
import { LoginPage } from './pages/Login.page';

const ProtectedRoutes = () => {
  const location = useLocation();
  if (authService.isUserLoggedIn()) {
    return <Outlet />;
  }
  return <Navigate to="/login" replace state={{ from: location }} />;
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
              element: <HomePage />,
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
            {
              path: 'page/:pageName',
              element: <CustomPage />,
            },
          ],
        },
        {
          path: '/protected',
          element: <div>secret vole</div>,
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
