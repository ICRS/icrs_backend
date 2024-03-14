import './App.css';

import {
  Route,
  Routes,
  Navigate
} from "react-router-dom";
import Registration from './pages/Registration/Registration';
import UserDetails from './pages/UserDetail/UserDetail';
import Root from "./routes/root";

import app_config from "./settings.json";
import AllUsers from './pages/Users/AllUsers';
import Login from './pages/Login/Login';
import { useState } from 'react';

function App() {
  const [login, setLogin] = useState(false);
  const [cookie, setCookie] = useState(null);

  return (
    <Routes>
      <Route path="/login" element={<Login loginHandler={setLogin} cookieHandler={setCookie} />} />
      {
        login && 
        <Route path="/" element={<Root />} >
          <Route path="/registration" element={<Registration endpoint={app_config["FORM_ENDPOINT"]} cookie={cookie} />} />
          <Route path="/user" element={<UserDetails endpoint={app_config["USER_ENDPOINT"]} cookie={cookie} />} />
          <Route path="/users/all" element={<AllUsers endpoint={app_config["ALL_USERS_ENDPOINT"]} cookie={cookie} />} />
        </Route> 
      }
      <Route path="*" element={<Navigate to="/login" />} />
    </Routes>
    // <RouterProvider router={router} />
  );
}

export default App;
