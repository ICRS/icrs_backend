function Form(props) {
    const handleSubmit = (e) => {
        e.preventDefault();

        const finalFormEndpoint = e.target.action;
        // console.log("Endpoint", finalFormEndpoint);
        const data = Array.from(e.target.elements)
            .filter((input) => input.name)
            .reduce((obj, input) => Object.assign(obj, { [input.name]: input.value }), {});
        
            data["print"] = data["print"] === "true";
        data["laser"] = data["laser"] === "true";

        fetch(finalFormEndpoint, {
            method: 'POST',
            headers: {
		    "Content-Type": "application/json",
                "Accept": "*/*",
            },
	body: JSON.stringify(data),
        })
            .then((response) => {
                if (!response.ok) {
                    return alert('User may not be registered.');
                }
            }).catch(() => {
                return alert('Could not submit form. Please try again later. Network or Server error likely.');
            });

    }

    return (
        <div className="form-box">
            <form
                action={props.endpoint}
                onSubmit={handleSubmit}
                method="POST"
                className="table-form" >
                <div className="pt-0 mb-3">
                    <label>Shortcode:</label>
                    <input
                        type="text"
                        name="shortcode" />
                </div>

                <div>
                    <label> Can Print: </label>
                    <select id="print" name="print">
                        <option value="true">True</option>
                        <option value="false">False</option>
                    </select>
                </div>

                <div className="pt-0 mb-3">
                    <label>Can Laser Cut:</label>
                    <select id="laser" name="laser">
                        <option value="false">False</option>
                        <option value="true">True</option>
                    </select>
                </div>
                <div>
                    <button type="submit">Submit</button>
                </div>
            </form>
        </div>
    );
};

function UpdatePermissions(props) {
    return (
        <div>
            <Form endpoint={props.endpoint} />
        </div>
    );
}

export default UpdatePermissions;
