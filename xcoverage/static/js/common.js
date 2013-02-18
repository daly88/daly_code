

function init_action()
{
$("#trace_list tr").hover(
	function() {
		$(this).addClass("tb_row_hover");
	},
	function() {
		$(this).removeClass("tb_row_hover");
	}
);

$("ul li").hover(
	function() {
		$(this).addClass("li_nav_hover");
	},
	function() {
		$(this).removeClass("li_nav_hover");
	}
);

}

$(document).ready(init_action);
