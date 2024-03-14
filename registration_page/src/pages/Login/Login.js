import { useNavigate } from 'react-router-dom';

function Login(props) {
    const navigate = useNavigate();

    const handleSubmit = (e) => {
        e.preventDefault();

        const finalFormEndpoint = e.target.action;
        // console.log("Endpoint", finalFormEndpoint);
        // const data = Array.from(e.target.elements)
        //     .filter((input) => input.name)
        //     .reduce((obj, input) => Object.assign(obj, { [input.name]: input.value }), {});
        // console.log("Data", data, JSON.stringify(data));

        fetch(finalFormEndpoint, {
            method: 'POST',
            headers: {
                "Accept": "*/*",
                "Authorization": "Basic aWNyczppY3Jz"
            },
			body: JSON.stringify({}),
            // redirect: 'follow',    
        })
            .then((response) => {
                if (!response.ok) {
                    return alert('User not registered. Membership may need to be acquired.');
                }
                // console.log(details);
                props.loginHandler(true);
                console.log(response)
                return navigate('/');
                // return alert("Success!");
            }).catch(() => {
                return alert('Could not submit form. Please try again later. Network error likely.');
            });

    }

    return (
        <div >
            <form 
                action="/api/login"
                method="POST"
                onSubmit={handleSubmit}
                >
                <div>
                    <label>Username</label>
                    <input type="text" placeholder="Username" />
                </div>
                <div>
                    <label>Password</label>
                    <input type="password" placeholder="Password" />
                </div>
                <button type="submit">Login</button>
            </form>
        </div>
    );
}

export default Login;