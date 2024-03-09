import { Outlet, Link } from "react-router-dom";

export default function Root() {
    return (
        <>
            <div id="sidebar">
                <h1>Navigation</h1>
                <nav>
                    <ul>
                        <li>
                            <Link to={`/`}> Home </Link>
                        </li>
                        <li>
                            <Link to={`/registration`} > Registration </Link>
                        </li>
                        <li>
                            <Link to={`/user`}> User Details/Permissions </Link>
                        </li>
                        <li>
                            <Link to={`/users/all`} > All Users </Link>
                        </li>
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