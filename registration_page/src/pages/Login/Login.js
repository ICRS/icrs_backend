import { useNavigate } from 'react-router-dom';
import './Login.css';

function Login(props) {
    const navigate = useNavigate();

    const handleSubmit = (endpoint) => {

        const finalFormEndpoint = endpoint;        
        fetch(finalFormEndpoint, {
            method: 'POST',
            headers: {
                "Accept": "*/*",
            },
        })
            .then((response) => {
                if (!response.ok) {
                    return alert('Invalid Login!!!');
                }
                console.log(response);
                props.loginHandler(true);
                console.log(response)
                return navigate('/');
            }).catch(() => {
                return alert('Could not log in! Network error likely.');
            });

    }
    handleSubmit(props.endpoint);
    
    return;
}

export default Login;