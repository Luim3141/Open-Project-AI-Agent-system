# Controller regression seam; synthetic bridge, no Rails session, database or provider.
require "active_support/all"
require "minitest/autorun"

class ApplicationController
  def self.before_action(*) = nil
  def self.authorize_with_permission(*) = nil
  attr_accessor :params, :rendered
  def helpers = self
  def qldapm_preview(_) = {title: "Synthetic confirmation"}
  def render(*args, **options)
    self.rendered = [args, options]
  end
end

class User
  def self.current = Struct.new(:admin?).new(false)
end

module Qldapm
  class AiBridge
    class << self
      attr_accessor :calls, :failure
      def call(_project, _actor, operation, command)
        action = operation == "confirm" ? "confirm" : command.fetch(:action)
        calls << action
        raise ArgumentError, "SYNTHETIC_DENIED" if failure == action
        result = case action
                 when "identity" then {"user_id" => 19, "role" => "PM"}
                 when "get_assistant_status" then {"gateway" => "ok", "openproject" => "authenticated"}
                 when "analyze" then {"count" => 329, "control_center" => {"fixture" => true}}
                 when "get_action_history" then {"runs" => [], "proposals" => []}
                 else {}
                 end
        {"result" => result}
      end
    end
  end
end

load ENV.fetch("QLDAPM_CONTROLLER_SOURCE", "/app/app/controllers/qldapm_ai_controller.rb")

class AssistantContextTest < Minitest::Test
  def setup
    @controller = QldapmAIController.new
    @controller.instance_variable_set(:@project, Object.new)
    @controller.params = {tool: "identity", arguments: "{}"}.with_indifferent_access
    Qldapm::AiBridge.calls = []
    Qldapm::AiBridge.failure = nil
  end

  def assert_context
    assert_equal "authenticated", @controller.instance_variable_get(:@connection)&.fetch("openproject")
    assert_equal 329, @controller.instance_variable_get(:@dashboard)&.fetch("count")
    assert_equal true, @controller.instance_variable_get(:@control_center)&.fetch("fixture")
  end

  def test_successful_read_keeps_dashboard_and_control_center
    @controller.command
    assert_equal 19, @controller.instance_variable_get(:@result).dig("result", "user_id")
    assert_context
    assert_equal 1, Qldapm::AiBridge.calls.count("identity"), "Never resend the submitted command"
  end

  def test_denied_command_retains_original_error_and_loads_context
    Qldapm::AiBridge.failure = "identity"
    @controller.command
    assert_equal "SYNTHETIC_DENIED", @controller.instance_variable_get(:@error)
    assert_equal :unprocessable_entity, @controller.rendered.last[:status]
    assert_context
    assert_equal 1, Qldapm::AiBridge.calls.count("identity")
  end

  def test_invalid_json_still_loads_read_only_context
    @controller.params[:arguments] = "{"
    @controller.command
    assert_includes @controller.instance_variable_get(:@error), "Arguments JSON"
    assert_context
    refute_includes Qldapm::AiBridge.calls, "identity"
  end

  def test_context_failure_never_overwrites_success_or_repeats_command
    Qldapm::AiBridge.failure = "get_assistant_status"
    @controller.command
    assert_equal 19, @controller.instance_variable_get(:@result).dig("result", "user_id")
    assert_nil @controller.instance_variable_get(:@error)
    assert_equal "SYNTHETIC_DENIED", @controller.instance_variable_get(:@context_error)
    assert_equal 1, Qldapm::AiBridge.calls.count("identity")
  end

  def test_confirmation_keeps_dashboard_without_replaying_confirmation
    @controller.params = {proposal_id: "synthetic", hash: "synthetic"}.with_indifferent_access
    @controller.confirm
    assert_context
    assert_equal 1, Qldapm::AiBridge.calls.count("confirm")
  end

  def test_denied_confirmation_keeps_error_and_dashboard
    @controller.params = {proposal_id: "synthetic", hash: "synthetic"}.with_indifferent_access
    Qldapm::AiBridge.failure = "confirm"
    @controller.confirm
    assert_context
    assert_equal "SYNTHETIC_DENIED", @controller.instance_variable_get(:@error)
    assert_equal 1, Qldapm::AiBridge.calls.count("confirm")
  end
end
