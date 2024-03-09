import './App.css';

import {
  createBrowserRouter,
  RouterProvider,
} from "react-router-dom";
import Registration from './pages/Registration/Registration';
import UserDetails from './pages/UserDetail/UserDetail';
import Root from "./routes/root";

import app_config from "./settings.json";
import AllUsers from './pages/Users/AllUsers';


const router = createBrowserRouter([
  {
    path: "/",
    element: <Root />,
    children: [{
      path: "registration",
      element: <Registration endpoint={app_config[ "FORM_ENDPOINT" ]} />
    },
    {
      path: "user",
      element: <UserDetails endpoint={app_config[ "USER_ENDPOINT" ]} />
    },
    {
      path: "users/all",
      element: <AllUsers endpoint={app_config[ "ALL_USERS_ENDPOINT" ]} />
    }
  ]
  },
  // {
  //   path: "/registration",
  //   element: <Registration />,
    
  // }
]);


function App() {
  return (
    <RouterProvider router={router} />
  );
}

export default App;
