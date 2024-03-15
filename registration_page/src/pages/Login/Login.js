import { useNavigate } from 'react-router-dom';
import { useState } from 'react';

function Login(props) {
    const navigate = useNavigate();
    
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();

        const finalFormEndpoint = e.target.action;
        // console.log("Endpoint", finalFormEndpoint);
        
        const authorization = "Basic " + btoa(username+ ":" + password);
        console.log(authorization, username, password);
        fetch(finalFormEndpoint, {
            method: 'POST',
            headers: {
                "Accept": "*/*",
                "Authorization": authorization,
            },
			body: JSON.stringify({}),
            // redirect: 'follow',    
        })
            .then((response) => {
                if (!response.ok) {
                    return alert('User not registered. Membership may need to be acquired.');
                }
                console.log(response);
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
                    <input type="text" placeholder="Username" onChange={(e) => setUsername(e.target.value)}/>
                </div>
                <div>
                    <label>Password</label>
                    <input type="password" placeholder="Password" onChange={(e) => setPassword(e.target.value)} />
                </div>
                <button type="submit">Login</button>
            </form>
        </div>
    );
}

export default Login;