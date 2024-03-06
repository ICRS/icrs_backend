import './App.css';
// import { Form } from './form/Form.js';
// import { BrowserRouter as Router, Switch, Route, createBrowserRouter, Link } from 'react-router-dom';
import {
  createBrowserRouter,
  RouterProvider,
} from "react-router-dom";
import Registration from './pages/Registration/registration';
import Root from "./routes/root";

const router = createBrowserRouter([
  {
    path: "/",
    element: <Root />,
    children: [{
      path: "registration",
      element: <Registration />
    }]
  },
  // {
  //   path: "/registration",
  //   element: <Registration />,
    
  // }
]);


function App() {
  return (
    <RouterProvider router={router} />
    // <div className="App">
    // </div>
  );
}

export default App;
