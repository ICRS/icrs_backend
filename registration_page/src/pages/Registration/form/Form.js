import useForm from "./UseForm";
import "./Form.css";

export function Form(props) {
    const { handleSubmit, status } = useForm({});
    const handleSub = (e) => {
        e.preventDefault();
        handleSubmit(e);
        // Clear input values
        document.getElementsByName("id")[0].value = "";
        document.getElementsByName("shortcode")[0].value = "";
        document.getElementsByName("secret")[0].value = "";
    }
    return (
        <div className="form-box">
            <form
                action={props.endpoint}
                onSubmit={handleSub}
                method="POST"
                className="table-form" >
                <div className="table-row">
                    <label className="table-cell">Card UID: </label>
                    <input
                        type="text"
                        name="id"
                        required
                    />
                </div>

                <div className="pt-0 mb-3">
                    <label>Shortcode:</label>
                    <input
                        type="text"
                        name="shortcode"
                        className="focus:outline-none focus:ring relative w-full px-3 py-3 text-sm text-gray-600 placeholder-gray-400 bg-white border-0 rounded shadow outline-none"
                        required
                    />
                </div>

                <div className="pt-0 mb-3">
                    <label>Secret:</label>
                    <input
                        type="password"
                        name="secret"
                        required
                    />
                </div>

                <div className="pt-0 mb-3">
                    <label>Can Laser Cut:</label>
                    <select id="canLaserCut" name="canLaserCut">
                        <option value="">False</option>
                        <option value="True">True</option>
                    </select>

                </div>

                <div className="pt-0 mb-3">
                    <label>Can Print:</label>
                    <select id="canPrint" name="canPrint">
                        <option value="True">True</option>
                        <option value="">False</option>
                    </select>
                </div>

                {status !== "loading" && (

                    <div className="pt-0 mb-3">
                        <button
                            className="active:bg-blue-600 hover:shadow-lg focus:outline-none px-6 py-3 mb-1 mr-1 text-sm font-bold text-white uppercase transition-all duration-150 ease-linear bg-blue-500 rounded shadow outline-none"
                            type="submit"
                        >
                            Submit
                        </button>
                    </div>
                )}
            </form>
        </div>
    );
};

export default Form;
