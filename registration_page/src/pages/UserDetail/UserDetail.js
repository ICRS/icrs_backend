import { useState } from "react";

function Form(props) {
    const { handleSubmit, details } = QueryUserDetail();
    // getUserPerms
    return (
        <div className="form-box">
            <form
                action={props.endpoint}
                onSubmit={handleSubmit}
                method="GET"
                className="table-form" >
                <div className="pt-0 mb-3">
                    <label>Shortcode:</label>
                    <input
                        type="text"
                        name="shortcode" />
                </div>
                <div>
                    <button type="submit">Submit</button>
                </div>
            </form>
            {details !== '' &&
                <div>
                    <ul>
					{Object.entries(details).map(([item, index]) => (
						<li > {item}: {index.toString()} </li>
					))}
				</ul>
                </div>
            }
        </div>
    );
};

function UserDetail(props) {
    return (
        <div>
            <Form endpoint={props.endpoint} />
        </div>
    );
}

function QueryUserDetail() {
    const [details, setDetails] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        setDetails('');

        const finalFormEndpoint = e.target.action;
        // console.log("Endpoint", finalFormEndpoint);
        const data = Array.from(e.target.elements)
            .filter((input) => input.name)
            .reduce((obj, input) => Object.assign(obj, { [input.name]: input.value }), {});
        // console.log("Data", data, JSON.stringify(data));
        console.log(finalFormEndpoint+`?${new URLSearchParams(data)}`);
        fetch(finalFormEndpoint+`?${new URLSearchParams(data)}`, {
            method: 'GET',
            headers: {
                "Accept": "*/*",
            },
        })
            .then((response) => {
                if (!response.ok) {
                    return alert('User not registered. Membership may need to be acquired.');
                }
                response.json().then((data) => {
                    console.log(data);
                    setDetails(data);
                });
            }).catch(() => {
                return alert('Could not submit form. Please try again later. Network error likely.');
            });

    }

    return { handleSubmit, details };

}

export default UserDetail;
