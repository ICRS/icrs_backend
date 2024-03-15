import { Form } from './form/Form.js';

function Registration(props) {
    return (
        // <>
            <div id="contact">
                <Form endpoint={props.endpoint}  />
            </div>
        // </>
    );
}

export default Registration;