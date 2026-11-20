module Qldapm
  module BoardPermissions
    def writable?(model, user)
      return false if Rbac.managed?(model.project) && !Rbac.pm?(model.project, user)
      super
    end
  end
end
