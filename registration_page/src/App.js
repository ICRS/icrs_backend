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
import UpdatePermissions from './pages/UpdatePermissions/UpdatePermissions';
import RecentlyInducted from './pages/Users/RecentlyInducted';

function App() {
    const [login, setLogin] = useState(false);

    return (
        <Routes>
            <Route path="/login" element={<Login loginHandler={setLogin} endpoint={app_config["LOGIN_ENDPOINT"]} />} />
            {
                login &&
                <Route path="/" element={<Root />} >
                    <Route path="/registration" element={<Registration endpoint={app_config["FORM_ENDPOINT"]} />} />
                    <Route path="/user/detail" element={<UserDetails endpoint={app_config["USER_ENDPOINT"]} />} />
                    <Route path="/user/permission" element={<UpdatePermissions endpoint={app_config["UPDATE_PERMISSION_ENDPOINT"]} />} />
                    <Route path="/users/inducted/all" element={<AllUsers endpoint={app_config["ALL_USERS_ENDPOINT"]} />} />
                    <Route path="/users/inducted/recent" element ={ <RecentlyInducted endpoint={app_config["RECENTLY_INDUCTED_ENDPOINT"]} registrationEndpoint={app_config["REREGISTER_USERS_ENDPOINT"]}/>} />
                </Route>
            }
            <Route path="*" element={<Navigate to="/login" />} />
        </Routes>
        // <RouterProvider router={router} />
    );
}

export default App;
