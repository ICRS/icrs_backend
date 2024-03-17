import { Outlet, Link } from "react-router-dom";

export default function Root() {
    return (
        <>
            <div id="sidebar">
                <h1>Navigation</h1>
                <nav>
                    <h3> Registration </h3>
                    <ul>
                        <li>
                            <Link to={`/registration`} > Registration </Link>
                        </li>
                    </ul>
                    <h3> Permissions </h3>
                    <ul>
                        <li>
                            <Link to={`/user/detail`}> Details/Permissions </Link>
                        </li>
                        <li>
                            <Link to={`/user/permission`}> Update Permissions </Link>
                        </li>
                    </ul>

                    <h3> Inductions </h3>
                    <ul>
                        <li>
                            <Link to={`/users/inducted/all`} > All Inducted Users </Link>
                        </li>
                        <li>
                            <Link to={`/users/inducted/recent`} > Recently Inducted Users </Link>
                        </li>
                    </ul>
                </nav>
            </div>
            <div>
                <Outlet />
            </div>
        </>
    );
}