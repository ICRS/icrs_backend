import { Outlet, Link } from "react-router-dom";

export default function Root() {
    return (
        <>
            <div id="sidebar">
                <h1>React Router Contacts</h1>
                <nav>
                    <ul>
                        <li>
                            <Link to={`/registration`}>Registration</Link>
                        </li>
                        {/* <li>
                <Link to={`/contacts/2`}>Your Friend</Link>
              </li> */}
                    </ul>
                </nav>
            </div>
            {/* <div id="detail"></div> */}
            <div>
                <Outlet />
            </div>
        </>
    );
}